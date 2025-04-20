import sys
import os
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QScrollArea,
    QListWidget, QListWidgetItem, QLineEdit, QFrame, QFileDialog, QMessageBox, QSizeGrip, QSizePolicy
)
from PyQt6.QtGui import QIcon, QAction, QFont, QPainter, QColor, QPixmap
from PyQt6.QtCore import Qt, QSize, QRect, QTimer, QDateTime

APP_NAME = "Shitty Planner"
DB_FILENAME = "database.db"
SETTINGS_FILENAME = "settings.json"
ICON_PATH = os.path.join(os.path.dirname(__file__), "icons", "save.svg")
STAR_ICON = os.path.join(os.path.dirname(__file__), "icons", "star_white.svg")
STAR_FILLED_ICON = os.path.join(os.path.dirname(__file__), "icons", "star_white_filled.svg")
CLOSE_ICON = os.path.join(os.path.dirname(__file__), "icons", "close.svg")
QUESTION_ICON = os.path.join(os.path.dirname(__file__), "icons", "question.svg")
PAYPAL_ICON = os.path.join(os.path.dirname(__file__), "icons", "paypal.svg")
BOOK_ICON = os.path.join(os.path.dirname(__file__), "icons", "book.svg")
AMAZON_ICON = os.path.join(os.path.dirname(__file__), "icons", "amazon_a.svg")

# Helper to get exe folder
def get_app_folder():
    return os.path.dirname(os.path.abspath(sys.argv[0]))

def get_db_path():
    return os.path.join(get_app_folder(), DB_FILENAME)

def get_settings_path():
    return os.path.join(get_app_folder(), SETTINGS_FILENAME)

class CategoryTaskDB:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        cur = self.conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            name TEXT NOT NULL,
            content TEXT DEFAULT '',
            important INTEGER DEFAULT 0,
            last_modified TEXT,
            FOREIGN KEY(category_id) REFERENCES categories(id)
        )''')
        self.conn.commit()

    def get_categories(self):
        cur = self.conn.cursor()
        cur.execute('SELECT id, name FROM categories')
        return cur.fetchall()

    def get_tasks(self, category_id):
        cur = self.conn.cursor()
        cur.execute('SELECT id, name, important FROM tasks WHERE category_id=? ORDER BY important DESC, id ASC', (category_id,))
        return cur.fetchall()

    def get_task_content(self, task_id):
        cur = self.conn.cursor()
        cur.execute('SELECT content FROM tasks WHERE id=?', (task_id,))
        row = cur.fetchone()
        return row[0] if row else ""

    def get_task_last_modified(self, task_id):
        cur = self.conn.cursor()
        cur.execute('SELECT last_modified FROM tasks WHERE id=?', (task_id,))
        row = cur.fetchone()
        return row[0] if row else ""

    def add_category(self, name="NEW CATEGORY"):
        cur = self.conn.cursor()
        cur.execute('INSERT INTO categories (name) VALUES (?)', (name,))
        self.conn.commit()
        return cur.lastrowid

    def add_task(self, category_id, name="NEW TASK"):
        cur = self.conn.cursor()
        cur.execute('INSERT INTO tasks (category_id, name) VALUES (?, ?)', (category_id, name))
        self.conn.commit()
        return cur.lastrowid

    def update_category_name(self, category_id, name):
        cur = self.conn.cursor()
        cur.execute('UPDATE categories SET name=? WHERE id=?', (name, category_id))
        self.conn.commit()

    def update_task_name(self, task_id, name):
        cur = self.conn.cursor()
        cur.execute('UPDATE tasks SET name=? WHERE id=?', (name, task_id))
        self.conn.commit()

    def update_task_content(self, task_id, content):
        cur = self.conn.cursor()
        cur.execute('UPDATE tasks SET content=? WHERE id=?', (content, task_id))
        self.conn.commit()

    def set_task_important(self, task_id, important):
        cur = self.conn.cursor()
        cur.execute('UPDATE tasks SET important=? WHERE id=?', (int(important), task_id))
        self.conn.commit()

    def update_task_last_modified(self, task_id, last_modified):
        cur = self.conn.cursor()
        cur.execute('UPDATE tasks SET last_modified=? WHERE id=?', (last_modified, task_id))
        self.conn.commit()

    def delete_task(self, task_id):
        cur = self.conn.cursor()
        cur.execute('DELETE FROM tasks WHERE id=?', (task_id,))
        self.conn.commit()

    def delete_category_and_tasks(self, cat_id):
        c = self.conn.cursor()
        c.execute('DELETE FROM tasks WHERE category_id=?', (cat_id,))
        c.execute('DELETE FROM categories WHERE id=?', (cat_id,))
        self.conn.commit()

    def save(self):
        self.conn.commit()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
        appico_path = os.path.join(exe_dir, "appico.ico")
        if os.path.exists(appico_path):
            self.setWindowIcon(QIcon(appico_path))
        self.setWindowTitle(APP_NAME)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(1000, 700)
        self.db = CategoryTaskDB(get_db_path())
        self.selected_category = None
        self.selected_task = None
        self.saved_this_session = False
        self._drag_pos = None
        self._resizing = False
        self._resize_dir = None
        self.save_content_timer = QTimer(self)
        self.save_content_timer.setInterval(500)
        self.save_content_timer.setSingleShot(True)
        self.save_content_timer.timeout.connect(self.save_task_content_actual)
        self.init_ui()
        self.load_categories()

    def button_style(self):
        return (
            "QPushButton, QLineEdit {"
            "background: #fff; color: #222; font-size: 18px; border-radius: 16px; border: 2px solid #222; padding: 5px 0; margin: 2px 0; font-family: serif;"
            "}"
            "QPushButton:hover { background: #d6d6d6; }"
            "QLineEdit { padding-left: 16px; }"
        )

    def load_categories(self):
        # Clear area
        while self.cat_task_area.count():
            item = self.cat_task_area.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        # Load from DB
        cats = self.db.get_categories()
        for cat_id, cat_name in cats:
            self.add_category_widget(cat_id, cat_name)

    def add_category_widget(self, cat_id, cat_name):
        cat_widget = QWidget()
        cat_layout = QVBoxLayout(cat_widget)
        cat_layout.setContentsMargins(0, 0, 0, 0)
        cat_layout.setSpacing(2)
        # Category button (always QPushButton)
        cat_btn = QPushButton(cat_name)
        cat_btn.setStyleSheet(self.button_style())
        cat_btn.setFixedHeight(36)
        cat_btn.setFont(self.font())
        cat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cat_btn.clicked.connect(lambda _, cid=cat_id: self.select_category(cid))
        cat_btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        cat_btn.customContextMenuRequested.connect(lambda _, cid=cat_id, btn=cat_btn: self.edit_category_name(cid, btn))
        cat_btn.mouseDoubleClickEvent = lambda e, cid=cat_id, btn=cat_btn: self.edit_category_name(cid, btn)
        cat_layout.addWidget(cat_btn)
        # Tasks
        tasks = self.db.get_tasks(cat_id)
        for task in tasks:
            task_id, task_name, important = task
            self.add_task_widget(cat_layout, cat_id, task_id, task_name, important)
        # Add Task button styled
        add_task_btn = QPushButton("ADD TASK")
        add_task_btn.setStyleSheet(self.button_style())
        add_task_btn.setFixedHeight(36)
        add_task_btn.setFont(self.font())
        add_task_btn.clicked.connect(lambda _, cid=cat_id: self.add_task(cid))
        cat_layout.addWidget(add_task_btn)
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #222; background: #222; height: 3px;")
        cat_layout.addWidget(divider)
        self.cat_task_area.addWidget(cat_widget)

    def add_task_widget(self, parent_layout, cat_id, task_id, task_name, important):
        task_widget = QWidget()
        task_layout = QHBoxLayout(task_widget)
        task_layout.setContentsMargins(0, 0, 0, 0)
        task_layout.setSpacing(2)
        # Star button
        star_btn = QPushButton()
        star_btn.setFixedSize(28, 28)
        star_btn.setIcon(QIcon(STAR_FILLED_ICON if important else STAR_ICON))
        star_btn.setIconSize(QSize(20, 20))
        star_btn.setStyleSheet("border: none; background: transparent;")
        star_btn.clicked.connect(lambda _, tid=task_id, btn=star_btn: self.toggle_task_important(tid, btn))
        task_layout.addWidget(star_btn)
        # Task button (always QPushButton)
        task_btn = QPushButton(task_name)
        task_btn.setStyleSheet(self.button_style())
        task_btn.setFixedHeight(32)
        task_btn.setFont(self.font())
        task_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        task_btn.clicked.connect(lambda _, tid=task_id: self.select_task(tid))
        task_btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        task_btn.customContextMenuRequested.connect(lambda _, tid=task_id, btn=task_btn: self.edit_task_name(tid, btn))
        task_btn.mouseDoubleClickEvent = lambda e, tid=task_id, btn=task_btn: self.edit_task_name(tid, btn)
        task_layout.addWidget(task_btn)
        parent_layout.addWidget(task_widget)

    def edit_category_name(self, cat_id, btn):
        old_name = btn.text()
        edit = QLineEdit(old_name)
        edit.setStyleSheet(self.button_style())
        edit.setFixedHeight(36)
        edit.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        edit.setFont(btn.font())
        edit.setFocus()
        def finish_edit():
            new_name = edit.text().strip()
            if new_name:
                self.db.update_category_name(cat_id, new_name)
            self.load_categories()
        edit.editingFinished.connect(finish_edit)
        btn.parentWidget().layout().replaceWidget(btn, edit)
        btn.deleteLater()
        edit.setFocus()

    def edit_task_name(self, task_id, btn):
        old_name = btn.text()
        edit = QLineEdit(old_name)
        edit.setStyleSheet(self.button_style())
        edit.setFixedHeight(32)
        edit.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        edit.setFont(btn.font())
        edit.setFocus()
        def finish_edit():
            new_name = edit.text().strip()
            if new_name:
                self.db.update_task_name(task_id, new_name)
            self.load_categories()
        edit.editingFinished.connect(finish_edit)
        btn.parentWidget().layout().replaceWidget(btn, edit)
        btn.deleteLater()
        edit.setFocus()

    def toggle_task_important(self, task_id, star_btn):
        # Toggle important
        cur_tasks = self.db.conn.execute('SELECT important FROM tasks WHERE id=?', (task_id,)).fetchone()
        important = 0 if cur_tasks and cur_tasks[0] else 1
        self.db.set_task_important(task_id, important)
        star_btn.setIcon(QIcon(STAR_FILLED_ICON if important else STAR_ICON))
        self.load_categories()

    def select_category(self, cat_id):
        self.selected_category = cat_id
        self.selected_task = None
        self.show_category_delete_button(cat_id)
        self.task_title.setText("")
        self.task_content.setText("")
        self.clear_task_editor()

    def select_task(self, task_id):
        self.selected_task = task_id
        name = None
        # Find name
        cats = self.db.get_categories()
        for cat_id, _ in cats:
            tasks = self.db.get_tasks(cat_id)
            for tid, tname, _ in tasks:
                if tid == task_id:
                    name = tname
                    break
        self.task_title.setText(name or "TASK")
        content = self.db.get_task_content(task_id)
        self.task_content.setText(content)
        last_modified = self.db.get_task_last_modified(task_id)
        self.show_task_last_modified(last_modified)
        self.add_task_delete_button()
        self.clear_category_delete_button()

    def add_category(self):
        cat_id = self.db.add_category()
        self.load_categories()

    def add_task(self, cat_id):
        task_id = self.db.add_task(cat_id)
        self.db.update_task_last_modified(task_id, QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm"))
        self.load_categories()

    def save_task_content(self):
        # Debounced save: restart timer on each text change
        self.save_content_timer.start()

    def save_task_content_actual(self):
        if self.selected_task:
            content = self.task_content.toPlainText()
            self.db.update_task_content(self.selected_task, content)
            self.db.update_task_last_modified(self.selected_task, QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm"))
            self.show_task_last_modified(QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm"))

    def save_all(self):
        self.db.save()
        self.saved_this_session = True
        self.show_save_label()

    def show_save_label(self):
        self.save_label.setText("Saved!")
        self.save_label.show()
        QTimer.singleShot(1000, self.save_label.hide)

    def init_ui(self):
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        # Left panel
        self.left_panel = QFrame()
        self.left_panel.setStyleSheet("background-color: #3A4352; border-radius: 10px;")
        self.left_panel.setMinimumWidth(320)
        self.left_panel.setSizePolicy(self.left_panel.sizePolicy().horizontalPolicy(), self.left_panel.sizePolicy().verticalPolicy())
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(10)
        # App title as tab (closer to top)
        self.title_label = QLabel(APP_NAME)
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; font-family: serif; color: #222; background: #EDEDED; border: 3px solid #222; border-radius: 12px; padding: 2px 12px;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setFixedHeight(40)
        self.title_label.setFixedWidth(280)
        left_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignTop)
        # Category/task area
        self.cat_task_area = QVBoxLayout()
        self.cat_task_area.setSpacing(8)
        left_layout.addLayout(self.cat_task_area)
        # Add Category button
        self.add_cat_btn = QPushButton("ADD CATEGORY")
        self.add_cat_btn.setStyleSheet(self.button_style())
        self.add_cat_btn.clicked.connect(self.add_category)
        left_layout.addWidget(self.add_cat_btn, alignment=Qt.AlignmentFlag.AlignBottom)
        # Save icon, question icon, and label
        save_row = QHBoxLayout()
        save_row.setContentsMargins(0, 0, 0, 0)
        save_row.setSpacing(6)
        self.save_btn = QPushButton()
        self.save_btn.setIcon(QIcon(ICON_PATH))
        self.save_btn.setIconSize(QSize(28, 28))
        self.save_btn.setFixedSize(38, 38)
        self.save_btn.setStyleSheet("border: none; background: transparent;")
        self.save_btn.clicked.connect(self.save_all)
        save_row.addWidget(self.save_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        # Question/help icon
        self.help_btn = QPushButton()
        self.help_btn.setIcon(QIcon(QUESTION_ICON))
        self.help_btn.setIconSize(QSize(28, 28))
        self.help_btn.setFixedSize(38, 38)
        self.help_btn.setStyleSheet("border: none; background: transparent;")
        self.help_btn.clicked.connect(self.show_help_dialog)
        save_row.addWidget(self.help_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        self.save_label = QLabel("")
        self.save_label.setStyleSheet("color: white; font-weight: bold; background: #222; border-radius: 8px; padding: 2px 12px; min-width: 0px; min-height: 0px;")
        self.save_label.setFixedHeight(24)
        self.save_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.save_label.hide()
        save_row.addWidget(self.save_label, alignment=Qt.AlignmentFlag.AlignLeft)
        save_row.addStretch(1)
        left_layout.addLayout(save_row)
        # Right panel
        self.right_panel = QFrame()
        self.right_panel.setStyleSheet("background-color: #fff; border-radius: 14px; border: 3px solid #222;")
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(12)
        # Top bar for close button inside white frame
        right_top_bar = QHBoxLayout()
        right_top_bar.setContentsMargins(0, 0, 0, 0)
        right_top_bar.setSpacing(0)
        right_top_bar.addStretch()
        self.close_btn = QPushButton()
        self.close_btn.setIcon(QIcon(CLOSE_ICON))
        self.close_btn.setIconSize(QSize(16, 16))
        self.close_btn.setFixedSize(22, 22)
        self.close_btn.setStyleSheet("QPushButton { color: #222; background: transparent; border: none; } QPushButton:hover { background: transparent; color: #a33; }")
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setToolTip("")
        self.close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        right_top_bar.addWidget(self.close_btn, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        right_layout.addLayout(right_top_bar)
        self.task_title = QLabel("TASK 1")
        self.task_title.setStyleSheet("font-size: 24px; font-weight: bold;")
        right_layout.addWidget(self.task_title)
        self.task_content = QTextEdit()
        self.task_content.setStyleSheet("font-size: 18px; background: #fff; border: 2px solid #222;")
        self.task_content.setMinimumHeight(350)
        self.task_content.textChanged.connect(self.save_task_content)
        right_layout.addWidget(self.task_content)
        self.right_panel_layout = right_layout
        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(self.right_panel)
        # Add QSizeGrip for resizing (bottom right corner)
        grip = QSizeGrip(self)
        main_layout.addWidget(grip, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        self.setLayout(main_layout)
        self.setMinimumSize(650, 500)
        self.setSizePolicy(self.sizePolicy().horizontalPolicy(), self.sizePolicy().verticalPolicy())

    def add_task_delete_button(self):
        # Only show in right panel when a task is selected
        if hasattr(self, 'task_delete_btn') and self.task_delete_btn:
            self.task_delete_btn.hide()
        self.task_delete_btn = QPushButton("✕")
        self.task_delete_btn.setFixedSize(20, 20)
        self.task_delete_btn.setStyleSheet(
            "QPushButton { color: #000; background: #fff; border: 1px solid #000; border-radius: 10px; font-size: 12px; } "
            "QPushButton:hover { color: #fff; background: #000; border: 1px solid #000; }"
        )
        self.task_delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.task_delete_btn.clicked.connect(self.delete_selected_task)
        self.right_panel_layout.addWidget(self.task_delete_btn, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

    def delete_selected_task(self):
        if self.selected_task:
            self.db.delete_task(self.selected_task)
            self.selected_task = None
            self.load_categories()
            self.clear_task_editor()

    def show_task_last_modified(self, last_modified):
        if hasattr(self, 'last_modified_label') and self.last_modified_label:
            self.last_modified_label.hide()
        self.last_modified_label = QLabel(f"Last modified: {last_modified}")
        self.last_modified_label.setStyleSheet("color: #888; font-size: 10px;")
        self.last_modified_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        self.right_panel_layout.addWidget(self.last_modified_label, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)

    def clear_task_editor(self):
        self.task_title.setText("")
        self.task_content.setText("")
        if hasattr(self, 'last_modified_label') and self.last_modified_label:
            self.last_modified_label.hide()
        if hasattr(self, 'task_delete_btn') and self.task_delete_btn:
            self.task_delete_btn.hide()

    def show_help_dialog(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
        from PyQt6.QtGui import QPixmap, QCursor
        import webbrowser
        dlg = QDialog(self)
        dlg.setWindowTitle("About Shitty Planner")
        dlg.setFixedWidth(400)
        layout = QVBoxLayout(dlg)
        label = QLabel("Made for my own shitty memory, shared freely for yours. You can always donate to my dumbass though or buy my shitty literature.")
        label.setWordWrap(True)
        label.setStyleSheet("font-size: 14px; color: #222;")
        layout.addWidget(label)
        icon_row = QHBoxLayout()
        # Paypal
        paypal_btn = QPushButton()
        paypal_btn.setIcon(QIcon(PAYPAL_ICON))
        paypal_btn.setIconSize(QSize(32, 32))
        paypal_btn.setFixedSize(38, 38)
        paypal_btn.setStyleSheet("border: none; background: transparent;")
        paypal_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        paypal_btn.clicked.connect(lambda: webbrowser.open("https://www.paypal.com/donate/?business=UBZJY8KHKKLGC&no_recurring=0&item_name=Why+are+you+doing+this?+Are+you+drunk?+&currency_code=USD"))
        icon_row.addWidget(paypal_btn)
        # Goodreads/book
        book_btn = QPushButton()
        book_btn.setIcon(QIcon(BOOK_ICON))
        book_btn.setIconSize(QSize(32, 32))
        book_btn.setFixedSize(38, 38)
        book_btn.setStyleSheet("border: none; background: transparent;")
        book_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        book_btn.clicked.connect(lambda: webbrowser.open("https://www.goodreads.com/book/show/25006763-usu"))
        icon_row.addWidget(book_btn)
        # Amazon
        amazon_btn = QPushButton()
        amazon_btn.setIcon(QIcon(AMAZON_ICON))
        amazon_btn.setIconSize(QSize(32, 32))
        amazon_btn.setFixedSize(38, 38)
        amazon_btn.setStyleSheet("border: none; background: transparent;")
        amazon_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        amazon_btn.clicked.connect(lambda: webbrowser.open("https://www.amazon.com/Usu-Jayde-Ver-Elst-ebook/dp/B00V8A5K7Y"))
        icon_row.addWidget(amazon_btn)
        icon_row.addStretch(1)
        layout.addLayout(icon_row)
        dlg.exec()

    def show_category_delete_button(self, cat_id):
        if hasattr(self, 'cat_delete_btn') and self.cat_delete_btn:
            self.cat_delete_btn.hide()
        self.cat_delete_btn = QPushButton("✕")
        self.cat_delete_btn.setFixedSize(20, 20)
        self.cat_delete_btn.setStyleSheet(
            "QPushButton { color: #000; background: #fff; border: 1px solid #000; border-radius: 10px; font-size: 12px; } "
            "QPushButton:hover { color: #fff; background: #000; border: 1px solid #000; }"
        )
        self.cat_delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cat_delete_btn.clicked.connect(lambda _, cid=cat_id: self.confirm_delete_category(cid))
        self.right_panel_layout.addWidget(self.cat_delete_btn, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)

    def clear_category_delete_button(self):
        if hasattr(self, 'cat_delete_btn') and self.cat_delete_btn:
            self.cat_delete_btn.hide()

    def confirm_delete_category(self, cat_id):
        msg = QMessageBox(self)
        msg.setWindowTitle("Delete Category")
        msg.setText("This will delete the category and ALL tasks under it. Continue?")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        res = msg.exec()
        if res == QMessageBox.StandardButton.Yes:
            self.db.delete_category_and_tasks(cat_id)
            self.load_categories()

    # ---- Frameless resizing support ----
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            if self._on_edge(event.pos()):
                self._resizing = True
                self._resize_dir = self._get_resize_dir(event.pos())
            else:
                self._resizing = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resizing and self._resize_dir:
            self._resize_window(event.globalPosition().toPoint())
        elif self._drag_pos and not self._resizing:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self._resizing = False
        self._resize_dir = None
        super().mouseReleaseEvent(event)

    def _on_edge(self, pos, margin=6):
        rect = self.rect()
        return (
            pos.x() < margin or pos.x() > rect.width() - margin or
            pos.y() < margin or pos.y() > rect.height() - margin
        )

    def _get_resize_dir(self, pos, margin=6):
        rect = self.rect()
        left = pos.x() < margin
        right = pos.x() > rect.width() - margin
        top = pos.y() < margin
        bottom = pos.y() > rect.height() - margin
        return (left, right, top, bottom)

    def _resize_window(self, global_pos):
        g = self.geometry()
        dx = global_pos.x() - g.x()
        dy = global_pos.y() - g.y()
        left, right, top, bottom = self._resize_dir
        min_w, min_h = self.minimumWidth(), self.minimumHeight()
        if left:
            new_x = min(g.x() + dx, g.right() - min_w)
            new_w = max(g.width() - dx, min_w)
            self.setGeometry(new_x, g.y(), new_w, g.height())
        if right:
            self.resize(max(dx, min_w), g.height())
        if top:
            new_y = min(g.y() + dy, g.bottom() - min_h)
            new_h = max(g.height() - dy, min_h)
            self.setGeometry(g.x(), new_y, g.width(), new_h)
        if bottom:
            self.resize(g.width(), max(dy, min_h))

    def closeEvent(self, event):
        if not self.saved_this_session:
            msg = QMessageBox(self)
            msg.setWindowTitle("Unsaved Changes")
            msg.setText("You have unsaved changes. What would you like to do?")
            save_exit = msg.addButton("Save and Exit", QMessageBox.ButtonRole.AcceptRole)
            exit_anyway = msg.addButton("Exit Anyway", QMessageBox.ButtonRole.DestructiveRole)
            msg.setDefaultButton(save_exit)
            msg.exec()
            if msg.clickedButton() == save_exit:
                self.save_all()
                event.accept()
            elif msg.clickedButton() == exit_anyway:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
