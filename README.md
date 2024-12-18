# Emailer Library

The `emailer` library provides functionality for sending emails using Flask and Jinja2 templates. It includes classes for managing email jobs, sending emails asynchronously, and queuing email tasks for later processing.

---

## Installation

To install the `emailer` library, run the following command:

```bash
pip install git+https://github.com/botsarefuture/emailer.git
```

---

## Features

- Asynchronous email sending with a background worker.
- Support for templated emails using Jinja2.
- Queueing system to handle email tasks efficiently.
- Customizable sender configurations.

---

## Usage

### Initialization

Create an instance of `EmailSender` by providing your application configuration:

```python
from emailer.EmailSender import EmailSender

config = {
    "MAIL_SERVER": "smtp.example.com",
    "MAIL_PORT": 587,
    "MAIL_USERNAME": "your_username",
    "MAIL_PASSWORD": "your_password",
    "MAIL_USE_TLS": True,
    "MAIL_DEFAULT_SENDER": "noreply@example.com",
    "DB_URI": "mongodb://localhost:27017/email_db"
}

email_sender = EmailSender(config)
```

---

## Methods

### `__init__(config)`

Initialize an `EmailSender` instance with Flask configuration, database connection, and email templates.

- **Parameters**:
  - `config` (`dict`): The configuration dictionary for the email sender.

---

### `start_worker()`

Start a background thread to process the email job queue.

> **Note:**
> This is automatically called when the `EmailSender` instance is created.

---

### `process_queue()`

Continuously process email jobs from the queue and send them. The queue is checked every 5 seconds.

> **Note:**
> This method is called by the background worker thread.

---

### `send_email(email_job)`

Send an email using the details from an `EmailJob` instance.

- **Parameters**:
  - `email_job` (`EmailJob`): Instance of `EmailJob` containing email details.

---

### `queue_email(template_name, subject, recipients, context, sender=None)`

Queue an email for sending using a Jinja2 template and context variables.

- **Parameters**:
  - `template_name` (`str`): Name of the Jinja2 template file.
  - `subject` (`str`): Subject of the email.
  - `recipients` (`list[str]`): List of recipient email addresses.
  - `context` (`dict`): Context variables for rendering the email template.
  - `sender` (`Sender`, optional): Optional sender details.

> **Note:**
> Use this instead of `send_now` to send emails efficiently.

---

### `send_now(template_name, subject, recipients, context, sender=None)`

Send an email immediately without queueing, using a Jinja2 template and context variables.

- **Parameters**:
  - `template_name` (`str`): Name of the Jinja2 template file.
  - `subject` (`str`): Subject of the email.
  - `recipients` (`list[str]`): List of recipient email addresses.
  - `context` (`dict`): Context variables for rendering the email template.
  - `sender` (`Sender`, optional): Optional sender details.

---

## Class: `Sender`

### Description

The `Sender` class holds SMTP server details and authentication credentials for sending emails.

### Attributes

- **_email_server** (`str`): The SMTP server address.
- **_email_port** (`int`): The port number for the SMTP server.
- **_username** (`str`): The username for SMTP authentication.
- **_password** (`str`): The password for SMTP authentication.
- **_use_tls** (`bool`): Whether to use TLS for the SMTP connection.
- **_email_address** (`str`): The sender's email address.
- **_display_name** (`str`): The display name of the sender.

### Methods

#### `__init__(email_server, email_port, username, password, use_tls, email_address, display_name=None)`

Initialize the `Sender` instance with SMTP server and authentication details.

- **Parameters**:
  - `email_server` (`str`): SMTP server address.
  - `email_port` (`int`): Port number for the SMTP connection.
  - `username` (`str`): Username for SMTP authentication.
  - `password` (`str`): Password for SMTP authentication.
  - `use_tls` (`bool`): Flag to use TLS.
  - `email_address` (`str`): Sender's email address.
  - `display_name` (`str`, optional): Display name of the sender.

---

#### `to_dict()`

Convert the `Sender` instance to a dictionary.

- **Returns**:
  - `dict`: A dictionary containing the sender's details.

---

#### `from_dict(data)`

Create a `Sender` instance from a dictionary.

- **Parameters**:
  - `data` (`dict`): Dictionary with sender details.

- **Returns**:
  - `Sender`: A new `Sender` instance.

---

## Class: `EmailJob`

### Description

The `EmailJob` class represents an email task, encapsulating information such as subject, recipients, email body, and sender.

### Attributes

- **_subject** (`str`): The subject line of the email.
- **_recipients** (`list[str]`): List of recipient email addresses.
- **_body** (`str`, optional): Plain text email content.
- **_html** (`str`, optional): HTML email content.
- **_sender** (`Sender`, optional): The sender details.

### Methods

#### `__init__(subject, recipients, body=None, html=None, sender=None)`

Initialize an `EmailJob` instance with email details.

- **Parameters**:
  - `subject` (`str`): Subject of the email.
  - `recipients` (`list[str]`): List of recipient email addresses.
  - `body` (`str`, optional): Plain text email content.
  - `html` (`str`, optional): HTML email content.
  - `sender` (`Sender`, optional): Sender details.

---

#### `to_dict()`

Convert the `EmailJob` instance to a dictionary.

- **Returns**:
  - `dict`: A dictionary representation of the email job.

---

#### `from_dict(data)`

Create an `EmailJob` instance from a dictionary.

- **Parameters**:
  - `data` (`dict`): Dictionary with email job details.

- **Returns**:
  - `EmailJob`: A new `EmailJob` instance.

---

## Logging

Logging is used to track the status and errors of email sending tasks. Configure the logger in your application to view debug and error messages:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
```

---

## Templates

Place your email templates in the `templates/emails/` directory. Use Jinja2 syntax to create dynamic email content.

Example:

```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ subject }}</title>
</head>
<body>
    <p>Hello {{ name }},</p>
    <p>Thank you for signing up!</p>
</body>
</html>
```

---

## Notes

- Ensure your MongoDB server is running for the email queue to function.
- Default sender details must be configured in the application config if not provided for each email.
- The `EmailSender` class uses threading for background processing, ensuring non-blocking operations.
