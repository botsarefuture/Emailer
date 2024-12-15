import threading
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader
from DatabaseManager import DatabaseManager
from .EmailJob import EmailJob, Sender
import time
import logging

logger = logging.getLogger(__name__)

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
        
        if hasattr(self._config, "MAIL_DEFAULT_SENDER"):
            self.default_sender = Sender(self._config.MAIL_SERVER, self._config.MAIL_PORT, self._config.MAIL_USERNAME, self._config.MAIL_PASSWORD, self._config.MAIL_USE_TLS, self._config.MAIL_DEFAULT_SENDER)
        else:
            self.default_sender = None

        self.start_worker()

    def start_worker(self):
        """
        Starts a background thread to process the email queue.
        """
        logger.info("Starting email queue worker thread.")
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
                logger.info("Processing email job from queue.")
                email_job = EmailJob.from_dict(email_job_data)
                self.send_email(email_job)
            else:
                logger.debug("No email job found in queue.")
            time.sleep(5)  # Sleep for 5 seconds before checking the queue again

    def send_email(self, email_job):
        """
        Sends an email using the details from the EmailJob instance.

        Parameters
        ----------
        email_job : EmailJob
            The EmailJob instance containing the email details.
            
        See Also
        --------
        RFC 822 section 6.1: https://datatracker.ietf.org/doc/html/rfc822.html#section-6.1
            This explains what kind of value can be used for the "From" field in an email.
        
        """
        try:
            # Determine SMTP settings and sender information
            sender = email_job.sender
            if sender is None:
                sender = self.default_sender
                
                if sender is None:
                    logger.error("No sender information provided. Fallback to default sender failed.")
                    return

        
            msg = MIMEMultipart("alternative")
            msg["Subject"] = email_job._subject
            msg["From"] = sender.get_sender_address()
            msg["To"] = ", ".join(email_job._recipients)

            if email_job._body:
                msg.attach(MIMEText(email_job._body, "plain"))
                
            if email_job._html:
                msg.attach(MIMEText(email_job._html, "html"))

            # Send the email using SMTP
            with smtplib.SMTP(sender._email_server, sender._email_port) as server:
                if sender._use_tls:
                    server.starttls()
                server.login(sender._username, sender._password)
                server.sendmail(sender.get_sender_address(), email_job._recipients, msg.as_string())
            logger.debug(f"Email sent to {email_job._recipients}")

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
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
        logger.debug(f"Queued email to {recipients} with subject '{subject}'")

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
        logger.debug(f"Sent email to {recipients} with subject '{subject}'")
