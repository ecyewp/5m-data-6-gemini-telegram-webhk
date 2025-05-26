
from flask import Flask, request, render_template
# import google.generativeai as genai
from google import genai
from dotenv import load_dotenv
import os
import sqlite3
import datetime
import requests


load_dotenv()
api_key=os.getenv("GEMINI_API_KEY")
api_key_tel=os.getenv("telegram_api_key")

# genai.configure(api_key=api_key) # Enter Your API Key
# model = genai.GenerativeModel("gemini-1.5-flash")

gemini_client = genai.Client(api_key=api_key_tel)
genmini_model = "gemini-2.0-flash"

url=f'https://api.telegram.org/bot{api_key_tel}'

app = Flask(__name__)

@app.route("/", methods=["GET","POST"])
def index():
    return(render_template("index.html"))

@app.route("/gemini", methods=["GET","POST"])
def gemini():
    return(render_template("gemini.html"))

@app.route("/gemini_reply", methods=["GET","POST"])
def gemini_reply():
    q = request.form.get("q")
    print(q)
    r = model.generate_content(q)
    return(render_template("gemini_reply.html",r=r.text))

@app.route("/main", methods=["GET","POST"])
def main():
    # Write into db
    name = request.form.get("q")
    t = datetime.datetime.now()
    if name!=None:
        conn = sqlite3.connect('user.db')
        c = conn.cursor()
        c.execute("insert into users(name,timestamp) values(?,?)",(name,t))
        conn.commit()
        c.close()
        conn.close()
    return(render_template("main.html"))

@app.route("/user_log", methods=["GET","POST"])
def user_log():
    # Read from DB
    conn = sqlite3.connect('user.db')
    c = conn.cursor()
    c.execute("SELECT * from users")
    r = c.fetchall()
    return(render_template("user_log.html", r=r))

@app.route("/delete_log", methods=["GET","POST"])
def delete_log():
    # Delete from DB
    conn = sqlite3.connect('user.db')
    c = conn.cursor()
    c.execute("delete from users")
    conn.commit()
    c.close()
    conn.close()
    return(render_template("delete_log.html"))

@app.route("/paynow", methods=["GET","POST"])
def paynow():
    return(render_template("paynow.html"))

# @app.route("/telegram", methods=["GET","POST"])
# def telegram():
#     return(render_template("telegram.html"))

@app.route("/prediction_reply", methods=["GET","POST"])
def prediction_reply():
    q = float(request.form.get("q"))
    print(q)
    return(render_template("prediction_reply.html",r=90.2 + (-50.6*q)))

@app.route("/start_telegram",methods=["GET","POST"])
def start_telegram():

    domain_url = os.getenv('WEBHOOK_URL')
    
    headers = {"Content-Type": "application/json"}
    payload = {"url": domain_url, "drop_pending_updates": True}

    # The following line is used to delete the existing webhook URL for the Telegram bot
    
    # delete_webhook_url = f"https://api.telegram.org/bot{api_key_tel}/deleteWebhook"
    # requests.post(delete_webhook_url, json={"url": domain_url, "drop_pending_updates": True})
    
    delete_webhook_url = f"https://api.telegram.org/bot{api_key_tel}/deleteWebhook" 
    requests.post(delete_webhook_url, json=payload, headers=headers)
    
    # Set the webhook URL for the Telegram bot
    set_webhook_url = f"https://api.telegram.org/bot{api_key_tel}/setWebhook?url={domain_url}/telegram"
    webhook_response = requests.post(set_webhook_url, json={"url": domain_url, "drop_pending_updates": True})
    print('webhook:', webhook_response)
    if webhook_response.status_code == 200:
        # set status message
        status = "The telegram bot is running. Please check with the telegram bot. @ttt_gemini_bot"
    else:
        status = "Failed to start the telegram bot. Please check the logs."
    
    return(render_template("telegram.html", status=status))

@app.route("/telegram",methods=["GET","POST"])
def telegram():
    update = request.get_json(force=True, silent=True)
    if "message" in update and "text" in update["message"]:
        # Extract the chat ID and message text from the update
        chat_id = update["message"]["chat"]["id"]
        text = update["message"]["text"]

        if text == "/start":
            r_text = "Welcome to the Gemini Telegram Bot! You can ask me any finance-related questions."
        else:
            # Process the message and generate a response
            system_prompt = "You are a financial expert.  Answer ONLY questions related to finance, economics, investing, and financial markets. If the question is not related to finance, state that you cannot answer it."
            prompt = f"{system_prompt}\n\nUser Query: {text}"
            r = genmini_client.models.generate_content(
                model=genmini_model,
                contents=prompt
            )
            r_text = r.text
        
        # Send the response back to the user
        send_message_url = f"https://api.telegram.org/bot{api_key_tel}/sendMessage"
        requests.post(send_message_url, data={"chat_id": chat_id, "text": r_text})
    # Return a 200 OK response to Telegram
    # This is important to acknowledge the receipt of the message
    # and prevent Telegram from resending the message
    # if the server doesn't respond in time
    return('ok', 200)

if __name__ == "__main__":
    app.run()
