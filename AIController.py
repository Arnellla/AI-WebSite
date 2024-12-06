import aiohttp
import openai
openai.api_key = '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'


async def get_answer(context, question, document_sources=None):
    try:
        if document_sources:
            document_info = "\n".join([f"Источник {i+1}: {source}" for i, source in enumerate(document_sources)])
            context_with_sources = f"Контекст (с источниками):\n{context}\n\nИсточники документов:\n{document_info}"
        else:
            context_with_sources = f"Контекст:\n{context}"

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": (
                    "Вы специалист по анализу текста и документов. "
                    "**ИЗВЛЕКАЙ ПО МАКСИМУМУ ПОЛЕЗНОЙ ИНФОРМАЦИИ ИЗ ТЕКСТА**. "
                    "ВАША ЗАДАЧА: отвечать максимально подробно и структурировано, используя каждую деталь текста. "
                    "Все ответы должны быть глубоко проработаны и объяснены. "
                    "Краткие или неполные ответы неприемлемы. "
                    "Ответ должен быть развёрнутым, полезным, с полным анализом и примерами, если это уместно. "
                    "Используйте каждый фрагмент контекста для формирования ответа. "
                    "Добавляйте ссылки на источники, если это возможно. "
                    "Максимум содержания, минимум воды. В конце добавьте короткую смешную фразу для завершения. "
                    "Ответ должен быть **минимум 8000 символов**."
	            "**ОБЯЗАТЕЛЬНО ДОЛЖНЫ УКАЗЫВАТЬСЯ ПУНКТЫ САМОГО ДОКУМЕНТА С КОТОРОГО БЫЛА ВЗЯТА ИНФОРМАЦИЯ НО ТОЛЬКО В ТОМ СЛУЧАЕ ЕСЛИ ТЫ УВЕРЕН ЧТО ЭТОТ ПУНКТ ВЕРЕН** **И САМ ДОКУМЕНТ ТОЖЕ ДОЛЖЕН ОбЯЗАН УКАЗАН БЫТЬ**"
                )},
                {"role": "user", "content": (
                    f"Изучите следующий текст и дайте максимально подробный, развёрнутый ответ с примерами, ссылками на источники и "
                    f"детализированными объяснениями. Текст должен быть тщательно проанализирован и структурирован. "
                    f"Краткие ответы неприемлемы. Ответ должен быть минимум на 8000 символов.\n\n"
                    f"Текст: {context_with_sources}\n\nВопрос: {question}"
                     "**ОБЯЗАТЕЛЬНО ДОЛЖНЫ УКАЗЫВАТЬСЯ ПУНКТЫ САМОГО ДОКУМЕНТА С КОТОРОГО БЫЛА ВЗЯТА ИНФОРМАЦИЯ НО ТОЛЬКО В ТОМ СЛУЧАЕ ЕСЛИ ТЫ УВЕРЕН ЧТО ПУНКТ ВЕРЕН!** **И САМ ДОКУМЕНТ ТОЖЕ ДОЛЖЕН ОбЯЗАН УКАЗАН БЫТЬ**"
                )}
            ],
            "max_tokens": 16000,
            "temperature": 0.0,
            "top_p": 1.0,
            "frequency_penalty": 0.2,
            "presence_penalty": 0.1,
        }

        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {openai.api_key}"}
            async with session.post('https://api.openai.com/v1/chat/completions', json=payload, headers=headers) as resp:

                if resp.status == 200:
                    response_data = await resp.json()

                    if 'choices' in response_data and response_data['choices']:
                        return response_data['choices'][0]['message']['content']
                    else:
                        return "Ошибка: Неправильная структура ответа от API"
                else:
                    response_text = await resp.text()
                    return f"Ошибка: {resp.status}, подробности: {response_text}"

    except aiohttp.ClientError as e:
        print(f"ClientError: {e}")
        return f"Ошибка при запросе к API: {e}"
    except Exception as e:
        print(f"Ошибка: {e}")
        return f"Неожиданная ошибка: {e}"

async def generate_main_answer(individual_answers, question):
    try:
        combined_answers = "\n\n".join(individual_answers)

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": (
                    "Вы помощник, который объединяет информацию из нескольких ответов. "
                    "ВАША ЗАДАЧА: на основе предоставленных ответов сформировать единый, максимально подробный и структурированный ответ. "
                    "Вы должны использовать **ТОЛЬКО** информацию из предоставленных ответов, **НЕ** добавляя ничего от себя. "
                    "Организуйте информацию логически, избегая повторений и противоречий. "
                    "Представляйте информацию в виде таблиц или списков для лучшей наглядности."
                    "Ответ должен быть на 7000 символов минимум, можно больше. "
                    "**ОБЯЗАТЕЛЬНО УКАЗЫВАЙ ПУНКТЫ ИЗ ЭТИХ ЖЕ ОТВЕТОВ НЕ МЕНЯЯ ИХ, ЧТОБЫ БЫЛО ПОНЯТНО ИЗ КАКОГО ДОКУМЕНТА БЫЛА ВЗЯТА ИНФОРМАЦИЯ И КАКОЙ ПУНКТ БЫЛ ИСПОЛЬЗОВАН**"
                )},
                {"role": "user", "content": (
                    f"Пожалуйста, объедините следующую информацию в единый, подробный ответ на заданный вопрос, **ЧЕМ КРУПНЕЕ ТЕМ ЛУЧШЕ, НО НИКАКОЙ ВОДЫ НЕ ДОБАВЛЯТЬ ОТ СЕБЯ**. "
                    f"Используйте **ТОЛЬКО** информацию из предоставленных ответов, **НЕ ДОБАВЛЯЯ НИЧЕГО НОВОГО**. "
                    f"**ПРЕДОСТАВЛЯЙТЕ ИНФОРМАЦИЮ ОБЯЗАТЕЛЬНО В ТАБЛИЦАХ ЕСЛИ ОНА УМЕСТНА И ПОДХОДИТ ДЛЯ ТАБЛИЦЫ. ОСТАЛЬНОЕ В СПИСКАХ**.\n\n"
                    f"Краткие ответы **НЕПРИЕМЛЕМЫ**. Ответ должен быть **МИНИМУМ НА 7000 СИМВОЛОВ**, можно больше.\n\n"
                    f"Ответы:\n{combined_answers}\n\nВопрос: {question}"
                     "**ОБЯЗАТЕЛЬНО УКАЗЫВАЙ ПУНКТЫ ИЗ ЭТИХ ЖЕ ОТВЕТОВ НЕ МЕНЯЯ ИХ, И УКАЗЫВАЙ ПУНКТ ТАК ЧТОБЫ ТЫ БЫЛ УВЕРЕН ЧТО ЭТО ИМЕННО ТОТ ПАРВИЛЬНЫЙ ПУНКТ КОТОРЫЙ ПОЛЬЗОВАТЕЛЬ ХОЧЕТ ВИДЕТЬ, ЧТОБЫ БЫЛО ПОНЯТНО ИЗ КАКОГО ДОКУМЕНТА БЫЛА ВЗЯТА ИНФОРМАЦИЯ И КАКОЙ ПУНКТ БЫЛ ИСПОЛЬЗОВАН**"
                )}
            ],
            "max_tokens": 12000,
            "temperature": 0.0,
            "top_p": 1.0,
            "frequency_penalty": 0.15,
            "presence_penalty": 0.05,
        }

        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {openai.api_key}"}
            async with session.post('https://api.openai.com/v1/chat/completions', json=payload, headers=headers) as resp:

                if resp.status == 200:
                    response_data = await resp.json()

                    if 'choices' in response_data and response_data['choices']:
                        return response_data['choices'][0]['message']['content']
                    else:
                        return "Ошибка: Неправильная структура ответа от API"
                else:
                    response_text = await resp.text()
                    return f"Ошибка: {resp.status}, подробности: {response_text}"

    except aiohttp.ClientError as e:
        print(f"ClientError: {e}")
        return f"Ошибка при запросе к API: {e}"
    except Exception as e:
        print(f"Ошибка: {e}")
        return f"Неожиданная ошибка: {e}"

