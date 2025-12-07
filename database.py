from flask_sqlalchemy import SQLAlchemy # импорт необходимой библиотеки

# создание объекта для работы с базой данных
db = SQLAlchemy()

# модель для списка покупок
class ShoppingList(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # уникальный id списка
    name = db.Column(db.String(100), default='Семейный список')  # название списка
    share_id = db.Column(db.String(10), unique=True, nullable=False)  # уникальная ссылка для доступа
    items = db.relationship('ListItem', backref='shopping_list', cascade='all, delete-orphan')  # связь с товарами
    created_at = db.Column(db.DateTime, default=db.func.now())  # дата создания

# модель для товара в списке
class ListItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # уникальный id товара
    text = db.Column(db.String(200), nullable=False)  # название товара
    quantity = db.Column(db.String(50), default='1')  # количество
    category = db.Column(db.String(100), default='Другое')  # категория (по умолчанию "Другое")
    added_by = db.Column(db.String(100), default='')  # кто добавил товар
    description = db.Column(db.Text)  # описание товара
    image_filename = db.Column(db.String(200))  # название файла изображения
    completed = db.Column(db.Boolean, default=False)  # отметка о покупке
    urgent = db.Column(db.Boolean, default=False)  # срочность
    list_id = db.Column(db.Integer, db.ForeignKey('shopping_list.id'), nullable=False)  # связь со списком
    created_at = db.Column(db.DateTime, default=db.func.now())  # дата добавления
