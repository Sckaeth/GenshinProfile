from io import BytesIO
from flask import Flask, send_file
from scripts.profiles import testrun

app = Flask(__name__)

def send_image():
    image = testrun()

    image_out = BytesIO()
    image.save(image_out, 'PNG')
    image_out.seek(0)
    return send_file(image_out, mimetype='image/png')

@app.route('/image')
def image():
    return send_image()

if __name__ == '__main__':
    app.run(debug=True)
