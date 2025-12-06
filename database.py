from flask_sqlalchemy import SQLAlchemy # импорт необходимой библиотеки

# Создание объекта для работы с базой данных
db = SQLAlchemy()

# Модель для списка покупок
class ShoppingList(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Уникальный id списка
    name = db.Column(db.String(100), default='Семейный список')  # Название списка
    share_id = db.Column(db.String(10), unique=True, nullable=False)  # Уникальная ссылка для доступа
    items = db.relationship('ListItem', backref='shopping_list', cascade='all, delete-orphan')  # Связь с товарами
    created_at = db.Column(db.DateTime, default=db.func.now())  # Дата создания

# Модель для товара в списке
class ListItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Уникальный id товара
    text = db.Column(db.String(200), nullable=False)  # Название товара
    quantity = db.Column(db.String(50), default='1')  # Количество
    category = db.Column(db.String(100), default='Другое')  # Категория (по умолчанию "Другое")
    added_by = db.Column(db.String(100), default='')  # Кто добавил товар
    description = db.Column(db.Text)  # Описание товара
    image_filename = db.Column(db.String(200))  # Название файла изображения
    completed = db.Column(db.Boolean, default=False)  # Отметка о покупке
    urgent = db.Column(db.Boolean, default=False)  # Срочность
    list_id = db.Column(db.Integer, db.ForeignKey('shopping_list.id'), nullable=False)  # Связь со списком
    created_at = db.Column(db.DateTime, default=db.func.now())  # Дата добавления