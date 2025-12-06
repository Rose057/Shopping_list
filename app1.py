# импорт библиотек
from flask import Flask, render_template, request, jsonify, redirect, url_for # импорт библиотек с фреймворком Flask, для рендеринга HTML-шаблонов, для преобразования данных в JSON, перенаправление на другие URL, генерации URL по имени функции
import secrets # нужен для генерации секретного ключа приложений и безопасного ID для общего доступа к списку
import os # нужен для работы с операционной системой (например, для работы с файловой системой)
from werkzeug.utils import secure_filename # нужен для преобразования небезопасных имен файлов
from database import db, ShoppingList, ListItem # импорт базы данных из отдельного файла
from datetime import timedelta # импорт библиотеки для работы со смещением времени

# конфигурация приложения
UPLOAD_FOLDER = 'static/uploads' # папка для хранения загружаемых изображений
ALLOWED_EXTENSIONS = {'png', 'jpeg', 'jpg', 'gif'} # разрешенные расширения файлов
MAX_FILE_SIZE = 8 * 1024 * 1024 # установка максимального размера изображений (8 МБ)

# создание основного приложения Flask
app = Flask(__name__)

# путь к базе данных
basedir = os.path.abspath(os.path.dirname(__file__))

# настройка приложения
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "shopping.db")}' # путь к базе данных
app.config['SECRET_KEY'] = secrets.token_hex(16) # секретный ключ для обеспечения безопасности
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, UPLOAD_FOLDER) # выбор папки для загрузок
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE # установка ограничения размера файлов

# создание папки для загрузок, если её нет
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# вспомогательная функция для проверки расширения файлов
def allowed_extensions(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# вспомогательная функция для сохранения загружаемого изображения
def save_uploaded_image(file):
    # проверка на существование файла, его имени и на допустимость расширения
    if not file or not file.filename or not allowed_extensions(file.filename):
        return None

    # создание безопасного имени файла с уникальным префиксом
    filename = secure_filename(f'{secrets.token_hex(8)}_{file.filename}')
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename) # создание пути к файлу
    file.save(file_path) # сохранение файла на сервер по указанному пути
    return filename # возвращает имя файла


# инициализация базы данных
# связывание базы данных с приложением
db.init_app(app)

# создание контекста приложения Flask для доступа к компонентам
with app.app_context():
    try:
        db.create_all() # автоматическое создание всех таблиц, если их нет
    except Exception as error:
        print(f'Ошибка настройки базы данных: {error}') # вывод сообщения об ошибке

# основные маршруты
# главная страница, которая демонстрирует форму создания нового списка
@app.route('/')
def home_page():
    return render_template('index.html')

# создание нового списка покупок и перенаправление на него
@app.route('/create_list', methods=['POST'])
def create_shopping_list():
    try:
        share_id = secrets.token_urlsafe(8)[:10] # генерация уникального ID для общего доступа
        # создание нового списка в базе данных
        new_list = ShoppingList(share_id=share_id)
        db.session.add(new_list)
        db.session.commit() # сохранение изменений в базе данных
        # перенаправление пользователя на созданный список
        return redirect(url_for('show_shopping_list', share_id=share_id))
    # вывод ошибки
    except Exception as error:
        return f'Ошибка при создании списка: {str(error)}', 500

# показывает страницу конкретного списка покупок
@app.route('/list/<share_id>')
def show_shopping_list(share_id):
    try:
        # нахождение списка по id или вывод ошибки 404, если не найден
        shopping_list = ShoppingList.query.filter_by(share_id=share_id).first_or_404()
        # демонстрация страницы с конкретным списком покупок
        return render_template('list.html', shopping_list=shopping_list)
    # вывод ошибки
    except Exception as error:
        return f"Ошибка загрузки списка: {str(error)}", 500

# API для работы с товарами
# обработка всех операций с товарами: получение, добавление, изменение
@app.route('/api/list/<share_id>/items', methods=['GET', 'POST', 'PUT'])
def manage_items(share_id):
    try:
        # нахождение списка по ID
        shopping_list = ShoppingList.query.filter_by(share_id=share_id).first_or_404()
        # в зависимости от типа запроса происходит вызов нужной функции
        if request.method == 'POST':
            return add_new_item(shopping_list) # добавление нового товара
        elif request.method == 'PUT':
            return update_existing_item(shopping_list) # изменение существующего товара
        else:
            # запрос GET возвращает все товары из списка
            items = [{
                'id': item.id, # id товара
                'text': item.text, # название товара
                'quantity': item.quantity, # количество товара
                'category': item.category, # категория товара
                'added_by': item.added_by, # кем добавлен товар
                'created_at': (item.created_at + timedelta(hours=3)).isoformat(), # время добавления товара (+3 часа)
                'description': item.description, # описание к товару
                'image_filename': item.image_filename, # название изображения
                'completed': item.completed, # совершена покупка или нет
                'urgent': item.urgent # срочность покупки
            } for item in shopping_list.items]

            return jsonify(items) # возвращаются данные в формате JSON
    # вывод ошибки
    except Exception as error:
        print(f'Ошибка в manage_items: {str(error)}')
        return jsonify({'error': str(error)}), 500

# функции для работы с товарами
# функция добавляет новый товар в список
def add_new_item(shopping_list):
    data = request.form # получение из формы данных, которые вводит пользователь

    # создание нового товара с данными из формы
    new_item = ListItem(text=data.get('text', '').strip(), # название товара (обязательное поле)
                        quantity=data.get('quantity', '1').strip(), # количество, по умолчанию '1'
                        category=data.get('category', 'Другое').strip(), # категория, по умолчанию 'другое'
                        added_by=data.get('added_by', '').strip(), # кем добавлен
                        description=data.get('description', '').strip(), # описание
                        urgent='urgent' in data, # срочность (проверка отмечено или нет)
                        shopping_list=shopping_list # привязка к списку
                        )

    # проверка, что название товара не пустое и вывод ошибки в случае отсутствия
    if not new_item.text:
        return jsonify({'error': 'Название товара обязательно'}), 400


    # обработка загрузкии изображения
    # сохранение загруженного изображение и получение имени файла
    filename = save_uploaded_image(request.files['image'])
    # если сохранение удается, то имя файла сохраняется в базу данных
    if filename:
        new_item.image_filename = filename

    try:
        # сохранение товара в базу данных
        db.session.add(new_item)
        db.session.commit() # сохранение изменений в базе данных
    # вывод ошибки
    except Exception as error:
        return jsonify({'error': f'Ошибка в базе данных: {str(error)}'}), 500

    # возвращение информации о созданном товаре
    return jsonify({
        'id': new_item.id, # id товара
        'text': new_item.text, # название
        'quantity': new_item.quantity, # количество
        'category': new_item.category, # категория
        'added_by': new_item.added_by, # кем добавлен
        'description': new_item.description, # описание
        'image_filename': new_item.image_filename, # название изображения
        'completed': new_item.completed, # совершена покупка или нет
        'urgent': new_item.urgent # срочность покупки
    })

# обновление информации о существующем товаре
def update_existing_item(shopping_list):
    data = request.form # получение данных из формы, которые отправляет браузер
    item_id = data.get('item_id') # извлечение id товара, требующего обновление

    # проверка, что id товара передан. Если его нет, то выводится ошибка
    if not item_id:
        return jsonify({'error': 'ID товара обязателен'}), 400

    # поиск товара в базе данных по id и по принадлежности к текущему списку
    item = ListItem.query.filter_by(id=item_id, shopping_list=shopping_list).first()
    # если товар не находится, то выводится ошибка
    if not item:
        return jsonify({'error': 'Товар не найден'}), 404

    # обновление всех полей товара
    item.text = data.get('text', '').strip()  # название товара (обязательное поле)
    item.quantity = data.get('quantity', '1').strip()  # количество, по умолчанию '1'
    item.category = data.get('category', 'Другое').strip()  # категория, по умолчанию 'другое'
    item.added_by = data.get('added_by', '').strip()  # кем добавлен
    item.description = data.get('description', '').strip()  # описание
    item.urgent = 'urgent' in data  # срочность (проверка отмечено или нет)

    # проверка, что есть название. Если его нет, то выводится ошибка
    if not item.text:
        return jsonify({'error': 'Название товара обязательно'}), 400

    # обработка загрузки изображения
    # сохранение загруженного изображения и получение имени файла
    filename = save_uploaded_image(request.files['image'])
    # проверка на успешное сохранение
    if filename:
        # удаление старого изображения, если оно есть
        if item.image_filename:
            # формировка полного пути к старому файлу
            old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], item.image_filename)
            # проверка, существует ли старый файл
            if os.path.exists(old_image_path):
                os.remove(old_image_path) # удаление старого файла с сервера

        item.image_filename = filename # сохранение имени файла в базу данных

    # удаление изображения, если пользователь нажал на кнопку удаления
    elif data.get('remove_image') == 'true':
        # проверка на существование изображения у товара
        if item.image_filename:
            # формировка полного пути к файлу
            old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], item.image_filename)  # создание пути к файлу
            # если файл существует, то он удаляется из папки
            if os.path.exists(old_image_path):
                os.remove(old_image_path)
            item.image_filename = None  # очищение поля в базе данных



    # сохранение изменений в базе данных
    db.session.commit()

    # возвращение обновленной информации о товаре
    return jsonify({
        'id': item.id,  # id товара
        'text': item.text,  # название
        'quantity': item.quantity,  # количество
        'category': item.category,  # категория
        'added_by': item.added_by,  # кем добавлен
        'description': item.description,  # описание
        'image_filename': item.image_filename,  # название изображения
        'completed': item.completed,  # совершена покупка или нет
        'urgent': item.urgent  # срочность покупки
    })

# API для операций с товарами
# обработка операций с отдельным товаром: отметка о покупке (PUT) и удаление (DELETE)
@app.route('/api/item/<int:item_id>', methods=['PUT', 'DELETE'])
def manage_item(item_id):
    # нахождение товара по id или ошибка 404
    item = ListItem.query.get_or_404(item_id)

    # если пользователь отмечает товар как купленный/некупленный
    if request.method == 'PUT':
        data = request.get_json() # получение данных в формате JSON
        # обновление статуса выполнения товара
        item.completed = data.get('completed', False) # берет значение completed из JSON или присваивает False по умолчанию
        db.session.commit() # сохранение изменений в базе данных
        return jsonify({'success': True}) # возвращение ответа в формате JSON об успешном выполнении

    # если пользователь удаляет товар
    elif request.method == 'DELETE':
        db.session.delete(item) # удаление товара из списка
        db.session.commit() # сохранение изменений в базе данных
        return jsonify({'success': True}) # возвращение ответа в формате JSON об успешном выполнении

# API для статистики
# возвращение статистики по списку: общее количество, купленные товары, по категориям
@app.route('/api/list/<share_id>/stats')
def get_statistics(share_id):
    try:
        # поиск списка покупок по share_id или вывод 404, если он не находится
        shopping_list = ShoppingList.query.filter_by(share_id=share_id).first_or_404()

        # подсчет общего количества товаров
        total_items = len(shopping_list.items)
        # подсчет количества купленных товаров
        completed_items = len([item for item in shopping_list.items if item.completed])
        # группировка товаров по категориям, создание словаря
        categories = {}
        # цикл по всем товарам в списке
        for item in shopping_list.items:
            # поиск категории (0, если новая), увеличение счетчика на 1 и добавление категории вместе с числом в словарь
            categories[item.category] = categories.get(item.category, 0) + 1

        # возвращение статистики в формате JSON
        return jsonify({
            'total_items': total_items, # общее количество товаров
            'completed_items': completed_items, # количество купленных товаров
            'categories': categories # словарь по категориям и количествам товаров в них
        })
    # обработка ошибок
    except Exception as error:
        return jsonify({'error': str(error)}), 500

# запуск приложения в режиме отладки
if __name__ == '__main__':
    app.run(debug=True)