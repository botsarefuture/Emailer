import threading
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader
from DatabaseManager import DatabaseManager
from .EmailJob import EmailJob
import time

class EmailSender:
    """
    The EmailSender class handles sending emails by processing email jobs from a queue.
    It uses SMTP to send emails and supports templated email content.
    """

    def __init__(self, config):
        """
        Initializes the EmailSender instance with the Flask app configuration.

        Parameters
        ----------
        config : dict
            The configuration dictionary for the email sender.
        """
        self._config = config
        self._db_manager = DatabaseManager(config)
        self._db = self._db_manager.get_db()
        self._queue_collection = self._db["email_queue"]
        self._env = Environment(loader=FileSystemLoader("templates/emails"))
        self.start_worker()

    def start_worker(self):
        """
        Starts a background thread to process the email queue.
        """
        worker_thread = threading.Thread(target=self.process_queue)
        worker_thread.daemon = True
        worker_thread.start()

    def process_queue(self):
        """
        Continuously processes email jobs from the queue and sends them.
        """
        while True:
            email_job_data = self._queue_collection.find_one_and_delete({})
            if email_job_data:
                email_job = EmailJob.from_dict(email_job_data)
                self.send_email(email_job)
            time.sleep(5)  # Sleep for 5 seconds before checking the queue again

    def send_email(self, email_job):
        """
        Sends an email using the details from the EmailJob instance.

        Parameters
        ----------
        email_job : EmailJob
            The EmailJob instance containing the email details.
        """
        try:
            # Determine SMTP settings and sender information
            if email_job.sender:
                sender_address = email_job.sender.email_address
                smtp_server = email_job.sender.email_server
                smtp_port = email_job.sender.email_port
                smtp_username = email_job.sender.username
                smtp_password = email_job.sender.password
                use_tls = email_job.sender.use_tls
            else:
                sender_address = self._config.MAIL_DEFAULT_SENDER
                smtp_server = self._config.MAIL_SERVER
                smtp_port = self._config.MAIL_PORT
                smtp_username = self._config.MAIL_USERNAME
                smtp_password = self._config.MAIL_PASSWORD
                use_tls = (
                    self._config.MAIL_USE_TLS or True
                )  # Default to True if not specified

            msg = MIMEMultipart("alternative")
            msg["Subject"] = email_job.subject
            msg["From"] = sender_address
            msg["To"] = ", ".join(email_job.recipients)

            if email_job.body:
                msg.attach(MIMEText(email_job.body, "plain"))
            if email_job.html:
                msg.attach(MIMEText(email_job.html, "html"))

            # Send the email using SMTP
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if use_tls:
                    server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(sender_address, email_job.recipients, msg.as_string())

        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            # Optionally, requeue the email or log the error

    def queue_email(self, template_name, subject, recipients, context, sender=None):
        """
        Queues an email for sending using the provided template and context.

        Parameters
        ----------
        template_name : str
            The name of the email template file.
        subject : str
            The subject of the email.
        recipients : list of str
            A list of recipient email addresses.
        context : dict
            A dictionary of context variables to render the email template.
        sender : Sender, optional
            An instance of the Sender class. Defaults to None.
        """
        template = self._env.get_template(template_name)
        body = template.render(context)
        email_job = EmailJob(
            subject=subject, recipients=recipients, body=body, html=body, sender=sender
        )
        self._queue_collection.insert_one(email_job.to_dict())

    def send_now(self, template_name, subject, recipients, context, sender=None):
        """
        Sends an email immediately using the provided template and context.

        Parameters
        ----------
        template_name : str
            The name of the email template file.
        subject : str
            The subject of the email.
        recipients : list of str
            A list of recipient email addresses.
        context : dict
            A dictionary of context variables to render the email template.
        sender : Sender, optional
            An instance of the Sender class. Defaults to None.
        """
        template = self._env.get_template(template_name)
        body = template.render(context)
        email_job = EmailJob(
            subject=subject, recipients=recipients, body=body, html=body, sender=sender
        )
        self.send_email(email_job)
