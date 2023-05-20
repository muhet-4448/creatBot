import telethon
from telethon.tl.custom import Button
from telethon import TelegramClient, events


import asyncio
import openai
import config

openai.api_key = config.openai_key

client = TelegramClient(config.session_name_bot, config.API_ID, config.API_HASH).start(bot_token=config.BOT_TOCKEN)

keyboard_stop = [[Button.inline("Stop and reset convo", b"stop")]]


# helper function
async def send_qsn_and_retrive_result(prompt, conv, keyboard):
    message = await conv.send_message(prompt, buttons = keyboard)

    # wait for the user
    tasks = [conv.wait_event(events.CallbackQuery()), conv.get_response()]
    done, _ = await asyncio.wait([asyncio.create_task(task) for task in tasks], return_when=asyncio.FIRST_COMPLETED)

    result = done.pop().result()
    await message.delete()

    if isinstance(result, events.CallbackQuery.Event):
        return None
    else:
        return result.message.strip()

@client.on(events.NewMessage(pattern="(?i)/start"))
async def handle_start_command(event):
        SENDER = event.sender_id

        try:
            prompt = "Hello! I'm capRol-ChatGPT-Bot,I'm ready to assist you with any Question you have."
            await client.send_message(SENDER, prompt)

            async with client.conversation(await event.get_chat(), exclusive=True, timeout=600) as conv:
                history = []

                while True:
                    prompt = "Please provide your input to capRol-ChatGPT-Bot"
                    user_input = await send_qsn_and_retrive_result(prompt, conv, keyboard_stop)

                    if user_input is None:
                      prompt = "Received.Convo will be reset. Type /start to start a new one!"
                      await client.send_message(SENDER, prompt)
                      break
                    else:
                      prompt = "Just a second..."
                      thinking_message = await client.send_message(SENDER, prompt)

                      history.append({"role":"user", "content": user_input})

                      chat_completion = openai.ChatCompletion.create(
                          model=config.model_engine,
                          messages=history,
                          max_tokens=500,
                          n=1,
                          temperature=0.1
                      )

                      response = chat_completion.choices[0].message.content

                      history.append({"role": "assistant", "content": response})
                      await  thinking_message.delete()
                      await client.send_message(SENDER, response, parse_mode='Markdown')

        except asyncio.TimeoutError:
            await client.send_message(SENDER,
                                      "<b>Conversation ended</b>\nIt's been too long since your last response. Please type /start to begin a new convo",
                                      parse_mode='html')
            return

        except telethon.errors.common.AlreadyInConversationError:
            pass

        except Exception as e:
            print(e)
            await client.send_message(SENDER,
                                      "<b>Conversation ended</b>\nSomething went wrong.Please type /start to begin a new convo",
                                      parse_mode='html')
            return


if __name__ == '__main__':
    print("Bot Started...")
    client.run_until_disconnected()