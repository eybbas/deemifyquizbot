import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Токен бота
TOKEN = "8277454755:AAEbAfJveeCNwDgmr3B7QyPDTJb5L56nUos"

# Состояния для ConversationHandler
CHOOSING_SUBJECT = 0
ANSWERING = 1

# Глобальные переменные для хранения вопросов
all_subjects = {}  # Словарь: {название предмета: список вопросов}

# Настройка предметов и файлов
SUBJECTS = {
    'Системное программирование Тест': 'questions_subject1.txt',
    'Эволюция Тест': 'questions_subject2.txt'
}

def load_questions(filename):
    """Загрузка вопросов из текстового файла"""
    questions = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            # Разделяем по пустым строкам
            question_blocks = content.strip().split('\n\n')
            
            for block in question_blocks:
                lines = block.strip().split('\n')
                if len(lines) >= 6:  # Вопрос + 4 варианта + правильный ответ
                    question_text = lines[0].replace('Вопрос:', '').strip()
                    options = []
                    for i in range(1, 5):
                        # Убираем А), Б), В), Г)
                        option = lines[i].split(')', 1)[1].strip() if ')' in lines[i] else lines[i].strip()
                        options.append(option)
                    
                    # Получаем правильный ответ
                    correct_line = lines[5].replace('Правильный ответ:', '').strip()
                    # Преобразуем А, Б, В, Г в индексы 0, 1, 2, 3
                    correct_mapping = {'А': 0, 'Б': 1, 'В': 2, 'Г': 3, 'A': 0, 'B': 1, 'C': 2, 'D': 3}
                    correct_index = correct_mapping.get(correct_line, 0)
                    
                    questions.append({
                        'question': question_text,
                        'options': options,
                        'correct': correct_index
                    })
        
        return questions
    except FileNotFoundError:
        logging.error(f"Файл {filename} не найден!")
        return []
    except Exception as e:
        logging.error(f"Ошибка при загрузке вопросов из {filename}: {e}")
        return []

def load_all_subjects():
    """Загрузка вопросов для всех предметов"""
    global all_subjects
    all_subjects = {}
    
    for subject_name, filename in SUBJECTS.items():
        questions = load_questions(filename)
        if questions:
            all_subjects[subject_name] = questions
            logging.info(f"✅ {subject_name}: загружено {len(questions)} вопросов")
        else:
            logging.warning(f"⚠️ {subject_name}: файл {filename} пуст или не найден")
    
    return len(all_subjects) > 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    success = load_all_subjects()
    
    if not success:
        await update.message.reply_text(
            "❌ Файлы с вопросами не найдены или пусты!\n\n"
            "Создайте файлы:\n"
            f"📄 {SUBJECTS['Предмет 1']}\n"
            f"📄 {SUBJECTS['Предмет 2']}\n\n"
            "в той же папке что и бот."
        )
        return
    
    subjects_info = "\n".join([f"📚 {name}: {len(questions)} вопросов" 
                                for name, questions in all_subjects.items()])
    
    await update.message.reply_text(
        f"👋 Привет! Я quiz-бот!\n\n"
        f"Загруженные предметы:\n{subjects_info}\n\n"
        f"Команды:\n"
        f"/quiz - Начать викторину\n"
        f"/reload - Перезагрузить вопросы из файлов\n"
        f"/help - Помощь"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    files_list = "\n".join([f"📄 {filename} - для {name}" 
                            for name, filename in SUBJECTS.items()])
    
    await update.message.reply_text(
        "📖 Инструкция:\n\n"
        f"1️⃣ Создайте файлы с вопросами:\n{files_list}\n\n"
        "2️⃣ Формат вопросов:\n\n"
        "Вопрос: Ваш вопрос?\n"
        "А) Вариант 1\n"
        "Б) Вариант 2\n"
        "В) Вариант 3\n"
        "Г) Вариант 4\n"
        "Правильный ответ: А\n\n"
        "3️⃣ Отделяйте вопросы пустой строкой\n"
        "4️⃣ Используйте /reload чтобы перезагрузить вопросы\n"
        "5️⃣ Используйте /quiz чтобы начать викторину"
    )

async def reload_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /reload - перезагрузка вопросов"""
    success = load_all_subjects()
    
    if success:
        subjects_info = "\n".join([f"📚 {name}: {len(questions)} вопросов" 
                                    for name, questions in all_subjects.items()])
        await update.message.reply_text(
            f"✅ Вопросы перезагружены!\n\n{subjects_info}"
        )
    else:
        await update.message.reply_text(
            "❌ Не удалось загрузить вопросы!\n"
            f"Проверьте файлы:\n" +
            "\n".join([f"📄 {filename}" for filename in SUBJECTS.values()])
        )

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало викторины - выбор предмета"""
    if not all_subjects:
        await update.message.reply_text(
            "❌ Вопросы не загружены!\n"
            "Используйте /reload для загрузки вопросов."
        )
        return ConversationHandler.END
    
    # Создаем клавиатуру с предметами
    keyboard = [[subject] for subject in all_subjects.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "📚 Выберите предмет для викторины:",
        reply_markup=reply_markup
    )
    return CHOOSING_SUBJECT

async def choose_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора предмета"""
    chosen_subject = update.message.text
    
    if chosen_subject not in all_subjects:
        await update.message.reply_text("❌ Пожалуйста, выберите предмет из списка!")
        return CHOOSING_SUBJECT
    
    # Сохраняем выбранный предмет и вопросы
    context.user_data['subject'] = chosen_subject
    context.user_data['questions'] = all_subjects[chosen_subject]
    context.user_data['current_question'] = 0
    context.user_data['correct_answers'] = 0
    context.user_data['total_questions'] = len(all_subjects[chosen_subject])
    
    await update.message.reply_text(
        f"📖 Выбран предмет: {chosen_subject}\n"
        f"📝 Вопросов: {context.user_data['total_questions']}\n\n"
        f"Начинаем!"
    )
    
    # Отправка первого вопроса
    return await send_question(update, context)

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка вопроса пользователю"""
    question_num = context.user_data['current_question']
    total = context.user_data['total_questions']
    questions = context.user_data['questions']
    
    if question_num >= total:
        # Викторина завершена
        correct = context.user_data['correct_answers']
        percentage = (correct / total) * 100
        subject = context.user_data['subject']
        
        result_text = (
            f"🎉 Викторина по предмету '{subject}' завершена!\n\n"
            f"📊 Результат: {correct}/{total} ({percentage:.1f}%)\n\n"
        )
        
        if percentage == 100:
            result_text += "🏆 Идеально! Все ответы правильные!"
        elif percentage >= 80:
            result_text += "👏 Отлично! Очень хороший результат!"
        elif percentage >= 60:
            result_text += "👍 Хорошо! Но есть куда расти."
        else:
            result_text += "📚 Нужно подучить материал."
        
        result_text += "\n\nИспользуйте /quiz чтобы начать заново!"
        
        await update.message.reply_text(result_text, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    
    # Получаем текущий вопрос
    question = questions[question_num]
    
    # Формируем клавиатуру с вариантами ответов
    keyboard = [[opt] for opt in question['options']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    question_text = (
        f"❓ Вопрос {question_num + 1}/{total}\n\n"
        f"{question['question']}"
    )
    
    await update.message.reply_text(question_text, reply_markup=reply_markup)
    return ANSWERING

async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка ответа пользователя"""
    user_answer = update.message.text
    question_num = context.user_data['current_question']
    questions = context.user_data['questions']
    question = questions[question_num]
    
    # Находим индекс ответа пользователя
    try:
        user_answer_index = question['options'].index(user_answer)
    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, выберите вариант из предложенных!")
        return ANSWERING
    
    # Проверяем правильность
    if user_answer_index == question['correct']:
        context.user_data['correct_answers'] += 1
        await update.message.reply_text("✅ Правильно!")
    else:
        correct_answer = question['options'][question['correct']]
        await update.message.reply_text(f"❌ Неправильно!\nПравильный ответ: {correct_answer}")
    
    # Переход к следующему вопросу
    context.user_data['current_question'] += 1
    return await send_question(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена викторины"""
    await update.message.reply_text(
        "Викторина отменена. Используйте /quiz чтобы начать заново!",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main():
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # ConversationHandler для викторины
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('quiz', start_quiz)],
        states={
            CHOOSING_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_subject)],
            ANSWERING: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reload", reload_questions))
    application.add_handler(conv_handler)
    
    # Загружаем вопросы при запуске
    print("🤖 Бот запущен!")
    print("\n📚 Настроенные предметы:")
    for subject_name, filename in SUBJECTS.items():
        print(f"  • {subject_name}: {filename}")
    
    print("\n⏳ Загрузка вопросов...")
    success = load_all_subjects()
    
    if success:
        print("\n✅ Вопросы успешно загружены:")
        for name, questions in all_subjects.items():
            print(f"  📖 {name}: {len(questions)} вопросов")
    else:
        print("\n⚠️ Вопросы не загружены! Создайте файлы с вопросами.")
    
    print("\n🚀 Бот готов к работе!\n")
    
    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
