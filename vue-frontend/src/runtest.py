from flask import Flask, render_template, send_from_directory, request, jsonify
import os
class CustomFlask(Flask):
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(dict(
        block_start_string='<%',
        block_end_string='%>',
        variable_start_string='%%',
        variable_end_string='%%',
        comment_start_string='<#',
        comment_end_string='#>',
    ))

app = CustomFlask('voting',
                  template_folder=os.path.abspath('.'),
                  static_folder=os.path.abspath('./static/'))

if __name__ == '__main__':
    host = os.environ.get("FLASK_RUN_HOST", "0.0.0.0")
    port = os.environ.get("FLASK_RUN_PORT", "5000")
    app.run(host=host, port=port)
