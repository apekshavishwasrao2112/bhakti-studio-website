from app import app
from database import init

init()

if __name__ == "__main__":
    app.run()