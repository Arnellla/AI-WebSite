import asyncio
import os
import re
import shutil
import traceback

import aiosqlite
from quart import Quart, send_file, session, redirect, url_for, render_template, request, jsonify, flash
import openai

import database
from AIController import get_answer, generate_main_answer
from TextController import process_txt, split_large_text_file, get_top_relevant_texts, vectorize_text_with_filenames
from converter import convert_pdf_to_txt, convert_docx_to_txt, convert_pptx_to_txt, convert_xlsx_to_txt, allowed_file, \
    create_zip_directory, convert_to_pdf
from database import get_user, get_db_connection, save_message, create_chat, init_db, get_user_chats

UPLOAD_FOLDER = 'uploads'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


openai.api_key = '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'
app = Quart(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.urandom(24)

@app.before_serving
async def startup():
    await init_db()


#---------------------------------------------------
#---------------------------------------------------
#---------------------------------------------------


@app.route('/')
async def index():
    try:
        return await render_template('index.html')
    except FileNotFoundError as e:
        print(f"Шаблон не найден: {e}")
        return "Ошибка: файл шаблона не найден.", 404
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return "Внутренняя ошибка сервера. Попробуйте позже.", 500

@app.route('/about')
async def about():
    try:
        return await render_template('about.html')
    except FileNotFoundError as e:
        print(f"Шаблон не найден: {e}")
        return "Ошибка: файл шаблона не найден.", 404
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return "Внутренняя ошибка сервера. Попробуйте позже.", 500

@app.errorhandler(404)
async def page_not_found(e):
    await flash('Страница не найдена', 'error')
    return redirect(url_for('index'))

@app.route('/login')
async def loginin():
    return await render_template('loginin.html')


@app.route('/chat')
async def chat():
    try:
        username = request.cookies.get('username')

        if not username:
            return redirect(url_for('loginin'))

        user = await get_user(username)

        if user:
            return await render_template('chat.html')
        else:
            print(f"Ошибка: пользователь с именем {username} не найден")
            return redirect(url_for('loginin'))

    except Exception as e:
        print(f"Произошла ошибка при авторизации: {e}")
        await flash('Iternal Server Error! Check server terminal.', 'error')
        return redirect(url_for('index'))

PASSWORD = "admin123"

app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024

@app.route('/admin', methods=['GET', 'POST'])
async def upload_file():
    try:
        if 'logged_in' not in session:
            if request.method == 'POST':
                form = await request.form
                password = form.get('password')

                if password == PASSWORD:
                    session['logged_in'] = True
                    return redirect(url_for('upload_file'))
                else:
                    return '''
                        <html>
                        <head>
                            <style>
                                body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                                .container { text-align: center; }
                                input, button { padding: 10px; margin: 10px 0; }
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <p>Неверный пароль. Попробуйте снова.</p>
                                <form method="POST">
                                    <input type="password" name="password" placeholder="Введите пароль" required>
                                    <button type="submit">Войти</button>
                                </form>
                            </div>
                        </body>
                        </html>
                    '''
            return '''
                <html>
                <head>
                    <style>
                        body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                        .container { text-align: center; }
                        input, button { padding: 10px; margin: 10px 0; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <form method="POST">
                            <input type="password" name="password" placeholder="Введите пароль" required>
                            <button type="submit">Войти</button>
                        </form>
                    </div>
                </body>
                </html>
            '''

        if request.method == 'POST':
            form = await request.form
            files = (await request.files).getlist('files')

            if 'create_directory' in form:
                dir_name = form.get('directory_name')

                if dir_name:
                    dir_path = os.path.join(app.config['UPLOAD_FOLDER'], dir_name)
                    if not os.path.exists(dir_path):
                        os.makedirs(dir_path)
                return redirect(url_for('upload_file'))

            if files:
                directory = form.get('directory')
                if not directory:
                    return redirect(url_for('upload_file'))

                output_folder = os.path.join(app.config['UPLOAD_FOLDER'], directory)
                if not os.path.exists(output_folder):
                    os.makedirs(output_folder)

                family_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'family&&&&&&&&')
                if not os.path.exists(family_folder):
                    os.makedirs(family_folder)

                async def process_file(file):
                    filename = file.filename.encode('utf-8').decode('utf-8', 'ignore')

                    file_path = os.path.join(output_folder, filename)
                    await file.save(file_path)

                    text_filename = filename

                    if filename.endswith('.pdf'):

                        text_filename = await convert_pdf_to_txt(file, output_folder)

                        family_pdf_path = os.path.join(family_folder, filename)
                        os.rename(file_path, family_pdf_path)

                        print(f"PDF файл перемещен в папку family: {family_pdf_path}")
                    else:

                        if filename.endswith('.docx'):
                            text_filename = await convert_docx_to_txt(file, output_folder)
                        elif filename.endswith('.pptx'):
                            text_filename = await convert_pptx_to_txt(file, output_folder)
                        elif filename.endswith('.xlsx'):
                            text_filename = await convert_xlsx_to_txt(file, output_folder)


                        if text_filename.endswith('.txt'):
                            text_filepath = os.path.join(output_folder, text_filename)
                            await split_large_text_file(text_filepath, output_folder)


                        pdf_filename = await convert_to_pdf(file_path, family_folder)

                        if pdf_filename:
                            print(f"Файл успешно конвертирован в PDF: {pdf_filename}")
                            try:
                                os.remove(file_path)
                                print(f"Исходный файл удален: {file_path}")
                            except Exception as e:
                                print(f"Ошибка при удалении исходного файла {file_path}: {e}")
                        else:
                            print(f"Ошибка при конвертации файла: {filename}")

                await asyncio.gather(*[process_file(file) for file in files if file.filename and allowed_file(file.filename)])

                return redirect(url_for('upload_file'))


        dirs = []
        for d in os.listdir(app.config['UPLOAD_FOLDER']):
            if os.path.isdir(os.path.join(app.config['UPLOAD_FOLDER'], d)) and d != 'family&&&&&&&&':
                files_in_dir = os.listdir(os.path.join(app.config['UPLOAD_FOLDER'], d))
                dirs.append({'name': d, 'files': files_in_dir})

        users = await get_all_users()

        return await render_template('admin.html', dirs=dirs, users=users)

    except FileNotFoundError as e:
        print(f"Ошибка: файл не найден - {str(e)}")
        await flash('Файл не найден.', 'error')
        return redirect(url_for('index'))
    except PermissionError as e:
        print(f"Ошибка: недостаточно прав - {str(e)}")
        await flash('Недостаточно прав.', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Произошла ошибка в админ панели: {str(e)}")
        await flash('Iternal Server Error! Check server terminal.', 'error')
        return redirect(url_for('index'))




@app.route('/move_file', methods=['POST'])
async def move_file():
    try:
        data = await request.get_json()
        filename = data.get('filename')
        from_directory = data.get('from_directory')
        to_directory = data.get('to_directory')

        if not filename or not from_directory or not to_directory:
            print("Ошибка: Необходимо указать файл, исходную и целевую директории.")
            return redirect(url_for('upload_file'))

        old_path = os.path.join(app.config['UPLOAD_FOLDER'], from_directory, filename)
        new_path = os.path.join(app.config['UPLOAD_FOLDER'], to_directory, filename)


        if os.path.exists(old_path):
            if not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], to_directory)):
                os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], to_directory))

            shutil.move(old_path, new_path)
            print(f"Файл {filename} успешно перемещен из {from_directory} в {to_directory}.")
        else:
            print(f"Ошибка: файл {filename} не найден в директории {from_directory}.")

        return redirect(url_for('upload_file'))
    except Exception as e:
        print(f"Произошла ошибка при перемещении файла: {str(e)}")
        return redirect(url_for('upload_file'))

@app.route('/create_directory', methods=['POST'])
async def create_directory():
    try:
        form = await request.form
        directory_name = form.get('directory_name')

        if not directory_name:
            print("Ошибка: Имя директории не указано.")
            return jsonify({'error': 'Имя директории обязательно'}), 400


        dir_path = os.path.join(app.config['UPLOAD_FOLDER'], directory_name)

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Директория {directory_name} успешно создана.")
            return redirect(url_for('upload_file'))
        else:
            print(f"Ошибка: Директория {directory_name} уже существует.")
            return redirect(url_for('upload_file'))

    except Exception as e:
        print(f"Произошла ошибка при создании директории: {str(e)}")
        await flash('Iternal Server Error! Check server terminal.', 'error')
        return redirect(url_for('index'))


@app.route('/create_user', methods=['POST'])
async def create_user_route():
    try:
        form = await request.form
        username = form.get('username')
        password = form.get('password')

        if not username or not password:
            print("Ошибка: Имя пользователя и пароль обязательны.")
            return redirect(url_for('upload_file'))

        await create_user(username, password)
        print(f"Пользователь {username} успешно создан.")
        return redirect(url_for('upload_file'))

    except Exception as e:
        print(f"Произошла ошибка при создании пользователя: {str(e)}")
        return redirect(url_for('upload_file'))


@app.route('/update_user', methods=['POST'])
async def update_user_route():
    try:
        form = await request.form
        user_id = form.get('user_id')
        new_username = form.get('new_username')
        new_password = form.get('new_password')

        if not user_id:
            print("Ошибка: ID пользователя обязателен.")
            return redirect(url_for('upload_file'))

        if not new_username and not new_password:
            print("Ошибка: Необходимо указать новое имя пользователя или пароль.")
            return redirect(url_for('upload_file'))

        await update_user(user_id, new_username, new_password)
        print(f"Пользователь с ID {user_id} успешно обновлён.")
        return redirect(url_for('upload_file'))

    except Exception as e:
        print(f"Произошла ошибка при обновлении пользователя: {str(e)}")
        await flash('Iternal Server Error! Check server terminal.', 'error')
        return redirect(url_for('index'))


@app.route('/delete_user', methods=['POST'])
async def delete_user_route():
    try:
        form = await request.form
        user_id = form.get('user_id')

        if not user_id:
            print("Ошибка: ID пользователя обязателен для удаления.")
            return redirect(url_for('upload_file'))

        await delete_user(user_id)
        print(f"Пользователь с ID {user_id} успешно удалён.")
        return redirect(url_for('upload_file'))

    except Exception as e:
        print(f"Произошла ошибка при удалении пользователя: {str(e)}")
        await flash('Iternal Server Error! Check server terminal.', 'error')
        return redirect(url_for('index'))


async def create_user(username, password):
    try:
        async with get_db_connection() as conn:
            await conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            await conn.commit()
            print(f"Пользователь {username} успешно создан.")
    except aiosqlite.IntegrityError:
        print(f"Ошибка: пользователь с именем {username} уже существует.")
    except Exception as e:
        print(f"Произошла ошибка при создании пользователя: {str(e)}")



async def get_all_users():
    try:
        async with get_db_connection() as conn:
            cursor = await conn.execute("SELECT id, username, password FROM users")
            users = await cursor.fetchall()

            return [{'id': row[0], 'username': row[1], 'password': row[2]} for row in users]
    except Exception as e:
        print(f"Ошибка при получении пользователей: {str(e)}")



async def update_user(user_id, new_username=None, new_password=None):
    try:
        async with get_db_connection() as conn:
            if new_username:
                await conn.execute("UPDATE users SET username = ? WHERE id = ?", (new_username, user_id))


            if new_password:
                await conn.execute("UPDATE users SET password = ? WHERE id = ?", (new_password, user_id))


            await conn.commit()
            print(f"Пользователь с ID {user_id} успешно обновлён.")
    except aiosqlite.IntegrityError as e:
        print(f"Ошибка при обновлении пользователя: {str(e)}")
    except Exception as e:
        print(f"Произошла ошибка при обновлении пользователя: {str(e)}")




async def delete_user(user_id):
    try:
        async with get_db_connection() as conn:

            await conn.execute("DELETE FROM users WHERE id = ?", (user_id,))


            await conn.commit()
            print(f"Пользователь с ID {user_id} успешно удалён.")
    except Exception as e:

        print(f"Произошла ошибка при удалении пользователя: {str(e)}")






@app.route('/download_file/<directory>/<filename>', methods=['GET'])
async def download_file(directory, filename):
    try:

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], directory, filename)


        if os.path.exists(file_path):
            return await send_file(file_path, as_attachment=True)
        else:
            print(f"Ошибка: файл {filename} не найден в директории {directory}.")
            return redirect(url_for('upload_file'))

    except Exception as e:
        print(f"Произошла ошибка при загрузке файла: {str(e)}")
        return redirect(url_for('upload_file'))

@app.route('/download_directory/<directory>', methods=['GET'])
async def download_directory(directory):
    try:
        family_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'family&&&&&&&&')

        target_dir = os.path.join(app.config['UPLOAD_FOLDER'], directory)

        if os.path.exists(target_dir):
            zip_file = create_zip_directory(target_dir, family_dir)
            return await send_file(zip_file, as_attachment=True, attachment_filename=f"{directory}_originals.zip", mimetype='application/zip')
        else:
            print(f"Ошибка: директория {target_dir} не найдена.")
            return redirect(url_for('upload_file'))

    except Exception as e:
        print(f"Произошла ошибка при загрузке директории: {str(e)}")
        return redirect(url_for('upload_file'))


@app.route('/delete_file', methods=['POST'])
async def delete_file():
    try:
        form = await request.form
        filename = form.get('filename')
        directory = form.get('directory')

        if not filename:
            print("Ошибка: имя файла не указано.")
            return redirect(url_for('upload_file'))

        if directory:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], directory, filename)
        else:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        file_path = os.path.normpath(file_path)

        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Файл {filename} успешно удалён.")
                return redirect(url_for('upload_file'))
            except Exception as e:
                print(f"Произошла ошибка при удалении файла: {str(e)}")
                return redirect(url_for('upload_file'))
        else:
            print(f"Ошибка: файл {filename} не найден.")
            return redirect(url_for('upload_file'))

    except Exception as e:
        print(f"Произошла ошибка при обработке запроса на удаление файла: {str(e)}")
        return redirect(url_for('upload_file'))

@app.route('/delete_directory', methods=['POST'])
async def delete_directory():
    try:
        form = await request.form
        directory = form.get('directory')

        if not directory:
            print("Ошибка: директория не указана.")
            return redirect(url_for('upload_file'))

        dir_path = os.path.join(app.config['UPLOAD_FOLDER'], directory)

        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            shutil.rmtree(dir_path)
            print(f"Директория {directory} успешно удалена.")
        else:
            print(f"Ошибка: директория {directory} не найдена.")

        return redirect(url_for('upload_file'))

    except Exception as e:
        print(f"Произошла ошибка при удалении директории: {str(e)}")
        return redirect(url_for('upload_file'))


@app.route('/rename_file', methods=['POST'])
async def rename_file():
    try:
        data = await request.form
        directory = data.get('directory')
        old_filename = data.get('filename')
        new_filename = data.get('new_filename')

        if not old_filename or not new_filename:
            print("Ошибка: старое и новое имена файла должны быть указаны.")
            return redirect(url_for('upload_file'))

        old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], directory, old_filename)
        new_filepath = os.path.join(app.config['UPLOAD_FOLDER'], directory, new_filename)

        if os.path.exists(new_filepath):
            print(f"Ошибка: файл с именем {new_filename} уже существует.")
            return redirect(url_for('upload_file'))

        os.rename(old_filepath, new_filepath)
        print(f"Файл {old_filename} успешно переименован в {new_filename}.")
        return redirect(url_for('upload_file'))

    except Exception as e:
        print(f"Произошла ошибка при переименовании файла: {str(e)}")
        return redirect(url_for('upload_file'))


@app.route('/rename_directory', methods=['POST'])
async def rename_directory():
    try:
        data = await request.form
        old_directory = data.get('directory')
        new_directory = data.get('new_directory_name')

        if not old_directory or not new_directory:
            print("Ошибка: старое и новое имена директории должны быть указаны.")
            return redirect(url_for('upload_file'))

        old_directory_path = os.path.join(app.config['UPLOAD_FOLDER'], old_directory)
        new_directory_path = os.path.join(app.config['UPLOAD_FOLDER'], new_directory)

        if os.path.exists(new_directory_path):
            print(f"Ошибка: директория с именем {new_directory} уже существует.")
            return redirect(url_for('upload_file'))

        os.rename(old_directory_path, new_directory_path)
        print(f"Директория {old_directory} успешно переименована в {new_directory}.")
        return redirect(url_for('upload_file'))

    except Exception as e:
        print(f"Произошла ошибка при переименовании директории: {str(e)}")
        return redirect(url_for('upload_file'))



#---------------------------------------------------
#---------------------------------------------------
#---------------------------------------------------

@app.route('/login', methods=['POST'])
async def login():
    try:
        data = await request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            print("Ошибка: Имя пользователя и пароль обязательны.")
            return jsonify({'error': 'Имя пользователя и пароль обязательны.'}), 400

        async with aiosqlite.connect('chat.db') as conn:
            cursor = await conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
            user = await cursor.fetchone()

        if user:
            response = jsonify({'success': True})
            response.set_cookie('username', username)
            print(f"Пользователь {username} успешно вошёл.")
            return response
        else:
            print("Ошибка: Неправильный логин или пароль.")
            return jsonify({'error': 'Неправильный логин или пароль'}), 401

    except Exception as e:
        print(f"Произошла ошибка при авторизации: {str(e)}")
        await flash('Iternal Server Error! Check server terminal.', 'error')
        return redirect(url_for('index'))


#---------------------------------------------------
#---------------------------------------------------
#---------------------------------------------------

@app.route('/view_file/<filename>', methods=['GET'])
async def view_file(filename):
    global extension
    try:
        family_folder = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], 'family&&&&&&&&')

        allowed_extensions = ['pdf', 'txt', 'docx', 'pptx', 'xlsx']
        file_path = None
        for ext in allowed_extensions:
            temp_path = os.path.join(family_folder, f"{filename}.{ext}")
            if os.path.exists(temp_path):
                file_path = temp_path
                extension = ext
                break

        if not file_path:
            await flash('Файл не найден на сервере.', 'error')
            return redirect(url_for('index'))

        print(f"Путь к файлу: {file_path}")

        if extension == 'pdf':
            content = f'<embed src="/uploads/family&&&&&&&&/{filename}.pdf" type="application/pdf" width="100%" height="100%" />'
        elif extension == 'txt':
            with open(file_path, 'r', encoding='utf-8') as file:
                file_content = file.read()
            content = f'<pre>{file_content}</pre>'
        elif extension in ['docx', 'pptx', 'xlsx']:
            pdf_path = await convert_to_pdf(file_path, family_folder)
            if pdf_path:
                return f'<embed src="/uploads/family&&&&&&&&/{os.path.basename(pdf_path)}" type="application/pdf" width="100%" height="100%" />'
            else:
                await flash('Файл не найден на сервере.', 'error')
                return redirect(url_for('index'))
        else:
            content = f'<a href="/uploads/family&&&&&&&&/{filename}.{extension}" download>Скачать {filename}.{extension}</a>'

        return f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{filename}</title>
            <style>
                body, html {{
                    margin: 0;
                    padding: 0;
                    height: 100%;
                    width: 100%;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }}
                pre {{
                    width: 100%;
                    height: 100%;
                    overflow: auto;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                }}
                embed {{
                    width: 100%;
                    height: 100%;
                    border: none;
                }}
            </style>
        </head>
        <body>
            {content}
        </body>
        </html>
        """
    except Exception as e:
        await flash('Iternal Server Error! Check server terminal.', 'error')
        return redirect(url_for('index'))


@app.route('/uploads/<path:filename>', methods=['GET'])
async def serve_uploaded_file(filename):
    try:
        file_path = os.path.join(app.root_path, 'uploads', filename)

        if os.path.exists(file_path) and os.path.isfile(file_path):
            return await send_file(file_path)
        else:
            print(f"Ошибка: файл {filename} не найден.")
            await flash('Файл не найден на сервере.', 'error')
            return redirect(url_for('index'))

    except Exception as e:
        print(f"Произошла ошибка при попытке отправить файл {filename}: {str(e)}")
        await flash('Iternal Server Error! Check server terminal.', 'error')
        return redirect(url_for('index'))

@app.route('/get_files', methods=['GET'])
async def get_files():
    try:
        folder_path = app.config['UPLOAD_FOLDER']

        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            print("Ошибка: директория для загрузок не найдена.")
            return jsonify({'error': 'Директория для загрузок не найдена'}), 404

        def get_directory_structure(path):
            directory_structure = {}
            for root, dirs, files in os.walk(path):
                rel_path = os.path.relpath(root, path)
                if rel_path == ".":
                    rel_path = ""
                directory_structure[rel_path] = files
            return directory_structure

        directory_structure = get_directory_structure(folder_path)
        return jsonify(directory_structure)

    except Exception as e:
        print(f"Произошла ошибка при получении списка файлов: {str(e)}")
        await flash('Iternal Server Error! Check server terminal.', 'error')
        return redirect(url_for('index'))

@app.route('/send_message_new', methods=['POST'])
async def send_message_new():
    try:
        data = await request.get_json()
        user_message = data.get('message')
        selected_document = data.get('document')
        selected_directories = data.get('directories')
        username = data.get('username')
        chat_name = data.get('chat_name')

        if not user_message:
            print("Ошибка: Сообщение пустое.")
            return jsonify({'response': 'Сообщение пустое'}), 400

        if not selected_document and not selected_directories:
            print("Ошибка: Документ или директория не выбраны.")
            return jsonify({'response': 'Документ или директория не выбраны'}), 400

        user = await get_user(username)
        if not user:
            print(f"Ошибка: Пользователь {username} не найден.")
            return jsonify({'response': 'Пользователь не найден'}), 404

        user_id = user[0]

        user_chats = await get_user_chats(user_id)

        if not user_chats:
            await create_chat(user_id, chat_name)
            user_chats = await get_user_chats(user_id)

        chat_id = user_chats[0][0]

        folder_path = os.path.abspath('uploads')
        all_selected_files = []

        if selected_document:
            if isinstance(selected_document, list):
                for doc in selected_document:
                    file_path = os.path.join(folder_path, doc)
                    if os.path.exists(file_path) and os.access(file_path, os.R_OK):
                        all_selected_files.append(doc)
                    else:
                        print(f"Ошибка: файл {doc} не найден или нет прав на доступ.")
                        await flash('Файл не найден, или нет прав на доступ', 'error')
                        return redirect(url_for('index'))
            else:
                file_path = os.path.join(folder_path, selected_document)
                if os.path.exists(file_path) and os.access(file_path, os.R_OK):
                    all_selected_files.append(selected_document)
                else:
                    print(f"Ошибка: файл {selected_document} не найден или нет прав на доступ.")
                    await flash('Файл не найден, или нет прав на доступ', 'error')
                    return redirect(url_for('index'))

        if selected_directories:
            for directory in selected_directories:
                dir_path = os.path.join(folder_path, directory)
                if os.path.exists(dir_path) and os.path.isdir(dir_path):
                    for file_name in os.listdir(dir_path):
                        file_path = os.path.join(dir_path, file_name)
                        if os.path.isfile(file_path) and os.access(file_path, os.R_OK):
                            all_selected_files.append(os.path.join(directory, file_name))

        if not all_selected_files:
            print("Ошибка: Нет доступных файлов для анализа.")
            return jsonify({'response': 'Нет доступных файлов для анализа'}), 400

        texts, filenames = process_txt(folder_path, specific_files=all_selected_files)
        if texts:
            vectorizer, text_matrix = vectorize_text_with_filenames(texts, filenames)
            top_texts, top_indices, top_filenames = get_top_relevant_texts(
                user_message, text_matrix, vectorizer, texts, filenames, top_n=3)

            await save_message(chat_id, user_id, user_message, sender="user")

            ai_messages = []
            tasks = []
            for idx, text in zip(top_indices, top_texts):
                tasks.append(get_answer(text, user_message))

            individual_answers = await asyncio.gather(*tasks)

            for idx, ai_message in zip(top_indices, individual_answers):
                file_name_with_extension = os.path.basename(filenames[idx])
                file_name = file_name_with_extension.replace(".txt", "")
                file_name = re.sub(r'_chap\d+$', '', file_name)
                file_url = f"/view_file/{file_name}"

                ai_message += f'\n(Основано на <a href="{file_url}" target="_blank">{file_name}</a>)'

                ai_messages.append(ai_message)

            final_answer = await generate_main_answer(ai_messages, user_message)

            source_info = []
            for idx in top_indices:
                file_name_with_extension = os.path.basename(filenames[idx])
                file_name = file_name_with_extension.replace(".txt", "")
                file_name = re.sub(r'_chap\d+$', '', file_name)
                file_url = f"/view_file/{file_name}"
                source_info.append(f'<a href="{file_url}" target="_blank">{file_name}</a>')

            if source_info:
                final_answer += '\n\nОсновано на: ' + ', '.join(source_info)

            await save_message(chat_id, user_id, final_answer, sender="ai")

            return jsonify({'response': final_answer})

        else:
            print("Ошибка: текст не найден в выбранных файлах.")
            return jsonify({'response': 'Ошибка: текст не найден в выбранных файлах'}), 400

    except Exception as e:
        traceback.print_exc()
        print(f"Произошла ошибка: {str(e)}")
        return jsonify({'error': str(e)}), 500



@app.route('/get_chat_history', methods=['GET'])
async def get_chat_history():
    try:
        username = request.cookies.get('username')

        if not username:
            print("Ошибка: Имя пользователя не предоставлено.")
            return jsonify({'response': 'Имя пользователя не предоставлено'}), 400

        user = await get_user(username)
        if not user:
            print(f"Ошибка: Пользователь {username} не найден.")
            return jsonify({'response': 'Пользователь не найден'}), 404

        user_id = user[0]

        user_chats = await get_user_chats(user_id)
        if not user_chats:
            print(f"Ошибка: У пользователя {username} нет чатов.")
            return jsonify({'response': 'У пользователя нет чатов'}), 404

        chat_id = user_chats[0][0]

        messages = await database.get_chat_history(chat_id, user_id)

        return jsonify({'messages': messages})

    except Exception as e:
        traceback.print_exc()
        print(f"Произошла ошибка: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)