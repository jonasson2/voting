FROM nikolaik/python-nodejs:latest

RUN mkdir -p /voting
COPY . /voting

WORKDIR /voting/vue-frontend
RUN npm install
RUN npm run build-production
# RUN sed -i 's/http:/https:/g' static/js/bundle.js

WORKDIR /voting/backend
ENV FLASK_DIGITAL_OCEAN=True
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000
RUN pip3 install -r requirements.txt

EXPOSE 5000

CMD ["python", "web.py"]
