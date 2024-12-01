# `emailer` Module Documentation

## Overview

The `emailer` module is responsible for managing and sending emails via SMTP. It includes three primary classes:

- `Sender`: Encapsulates SMTP server and sender information.
- `EmailJob`: Represents a single email task with subject, recipients, and content.
- `EmailSender`: Handles sending emails and processes email jobs from a queue in a background thread.

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

### Methods

#### `__init__(email_server, email_port, username, password, use_tls, email_address)`

Initialize the `Sender` instance with SMTP server and authentication details.

- **Parameters**:
  - `email_server` (`str`): SMTP server address.
  - `email_port` (`int`): Port number for the SMTP connection.
  - `username` (`str`): Username for SMTP authentication.
  - `password` (`str`): Password for SMTP authentication.
  - `use_tls` (`bool`): Flag to use TLS.
  - `email_address` (`str`): Sender's email address.

#### `to_dict()`

Convert the `Sender` instance to a dictionary.

- **Returns**:
  - `dict`: A dictionary containing the sender's details.

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

#### `to_dict()`

Convert the `EmailJob` instance to a dictionary.

- **Returns**:
  - `dict`: A dictionary representation of the email job.

#### `from_dict(data)`

Create an `EmailJob` instance from a dictionary.

- **Parameters**:
  - `data` (`dict`): Dictionary with email job details.

- **Returns**:
  - `EmailJob`: A new `EmailJob` instance.

---

## Class: `EmailSender`

### Description

The `EmailSender` class handles the process of sending emails, either directly or by queueing email jobs for background processing.

### Attributes

- **_config** (`Config`): Configuration for SMTP and email settings.
- **_db_manager** (`DatabaseManager`): Manages database connections.
- **_db** (`Database`): MongoDB database connection.
- **_queue_collection** (`Collection`): MongoDB collection for storing email jobs.
- **_env** (`Environment`): Jinja2 environment for rendering email templates.

### Methods

#### `__init__(config)`

Initialize an `EmailSender` instance with Flask configuration, database connection, and email templates.

- **Parameters**:
  - `config` (`dict`): The configuration dictionary for the email sender.

#### `start_worker()`

Start a background thread to process the email job queue.

#### `process_queue()`

Continuously process email jobs from the queue and send them. The queue is checked every 5 seconds.

#### `send_email(email_job)`

Send an email using the details from an `EmailJob` instance.

- **Parameters**:
  - `email_job` (`EmailJob`): Instance of `EmailJob` containing email details.

#### `queue_email(template_name, subject, recipients, context, sender=None)`

Queue an email for sending using a Jinja2 template and context variables.

- **Parameters**:
  - `template_name` (`str`): Name of the Jinja2 template file.
  - `subject` (`str`): Subject of the email.
  - `recipients` (`list[str]`): List of recipient email addresses.
  - `context` (`dict`): Context variables for rendering the email template.
  - `sender` (`Sender`, optional): Optional sender details.

#### `send_now(template_name, subject, recipients, context, sender=None)`

Send an email immediately without queueing, using a Jinja2 template and context variables.

- **Parameters**:
  - `template_name` (`str`): Name of the Jinja2 template file.
  - `subject` (`str`): Subject of the email.
  - `recipients` (`list[str]`): List of recipient email addresses.
  - `context` (`dict`): Context variables for rendering the email template.
  - `sender` (`Sender`, optional): Optional sender details.

---

## Example Usage

### Queueing an Email

```python
email_sender = EmailSender()

context = {
    "username": "John Doe",
    "event": "Weekly Meeting"
}

email_sender.queue_email(
    template_name="reminder_email.html",
    subject="Meeting Reminder",
    recipients=["user1@example.com", "user2@example.com"],
    context=context
)
```

### Sending an Email Immediately

```python
email_sender = EmailSender()

context = {
    "username": "John Doe",
    "event": "Weekly Meeting"
}

email_sender.send_now(
    template_name="reminder_email.html",
    subject="Meeting Reminder",
    recipients=["user1@example.com", "user2@example.com"],
    context=context
)
```

---

## Key Points

- **Background Processing**: `EmailSender` can process emails asynchronously using a queue.
- **Template Support**: It supports templated emails with Jinja2.
- **Error Handling**: The system catches and logs errors for troubleshooting.