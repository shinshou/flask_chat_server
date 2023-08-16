from flask_chat_server import app

if __name__ == ("__main__"):
    from dotenv import load_dotenv, find_dotenv

    load_dotenv(find_dotenv(), override=True)

    app.run(debug=True)
