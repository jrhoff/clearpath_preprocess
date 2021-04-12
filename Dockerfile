FROM python:3.6-slim



ADD ./setup.sh setup.sh
RUN ./setup.sh

# Add this entire directory into one called src/
ADD . /src
COPY nltk_data /root/nltk_data
# Set working directory
WORKDIR /src

# Expose
EXPOSE 5000

CMD ["python3", "app.py"]
