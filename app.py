from curses import color_content
from turtle import color
import chainlit as cl
from model.llm import chatbot_response


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Museum Inquiry",
            message="I would like to inquire about museums",
            #icon="./public/museum.png",
            ),

        cl.Starter(
            label="Book Tickets",
            message="I would like to book a ticket",
            #icon="./public/ticket.png",
            ),
        ]




#@cl.on_chat_start
#async def on_chat_start():
#    await cl.Message(
#        content=f"Hey There!\nWelcome to Online Ticketing System!\nHow can I help you today?",
#    ).send()



@cl.on_message
async def main(message: cl.Message):
    # Your custom LLM code logic goes here...
    response = chatbot_response(message.content)
    #print(response)
    #Sending a response back to the user 
    await cl.Message(
        content=f'<div style="background-color: #CEE6F2; padding: 15px; border-radius: 17px;">{response}</div>'
        ).send()






@cl.on_stop
async def on_stop():
    await cl.Message(
        content=f"You have manually stopped the task...",
    ).send()




@cl.on_chat_end
def on_chat_end():
    print("The user disconnected!")




