import threading
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader
from DatabaseManager import DatabaseManager
from .EmailJob import EmailJob, Sender
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from email.header import Header
import logging

logger = logging.getLogger(__name__)

def fix_from_header(from_address):
    """
    Fixes the encoding of the 'From' header to ensure it is properly formatted.
    
    Parameters
    ----------
    from_address : str
        The email address that needs to be fixed.
    
    Returns
    -------
    str
        The properly formatted 'From' header.
    """
    logger.debug(f"fix_from_header called with from_address: {from_address}")
    if from_address is None:
        return None

    # Handle the potential case where the 'From' address contains special characters or needs encoding
    if "<" in from_address and ">" in from_address:
        name, address = from_address.split("<")
        address = address.replace(">", "")
    else:
        name = ""
        address = from_address
    
    # Fix encoding if necessary
    name = name.strip()
    name_header = Header(name, "utf-8").encode()

    fixed_address = formataddr((name_header, address))
    logger.debug(f"Fixed 'From' address: {fixed_address}")
    return fixed_address


class EmailSender:
    """
    The EmailSender class handles sending emails by processing email jobs from a queue.
    It uses SMTP to send emails and supports templated email content.
    """

    def __init__(self, config, _config_2=None):
        """
        Initializes the EmailSender instance with the Flask app configuration.

        Parameters
        ----------
        config : dict
            The configuration dictionary for the email sender.
        """
        logger.debug(f"Initializing EmailSender with config: {config}")
        self._config = _config_2
        if self._config is None:
            self._config = {}
        print(config)
        self._db_manager = DatabaseManager(config).get_instance()
        self._db = self._db_manager.get_db()
        self._queue_collection = self._db["email_queue"]
        self._env = Environment(loader=FileSystemLoader("templates/emails"))
        
        
        if self._config.get("MAIL_DEFAULT_SENDER"):
            logger.info("Using default sender information from configuration.")
            self.default_sender = Sender(
                self._config.get('MAIL_SERVER'),
                self._config.get('MAIL_PORT'),
                self._config.get('MAIL_USERNAME'),
                self._config.get('MAIL_PASSWORD'),
                self._config.get('MAIL_USE_TLS'),
                self._config.get('MAIL_DEFAULT_SENDER')
            )
        else:
            logger.warning("No default sender information found in configuration.")
            self.default_sender = None
        
        self.register_filter()
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
            logger.debug("Checking email queue for jobs.")
            email_job_data = self._queue_collection.find_one_and_delete({})
            if email_job_data:
                logger.info("Processing email job from queue.")
                email_job = EmailJob.from_dict(email_job_data)
                self.send_email(email_job)
                logger.info("Processed.")
            else:
                logger.debug("No email job found in queue.")
            time.sleep(5)  # Sleep for 5 seconds before checking the queue again

    def send_email(self, email_job, send=True):
        """
        Sends an email using the details from the EmailJob instance.

        Parameters
        ----------
        email_job : EmailJob
            The EmailJob instance containing the email details.
        send : bool, optional
            If False, the email will not be sent. Defaults to True.
            
        See Also
        --------
        RFC 822 section 6.1: https://datatracker.ietf.org/doc/html/rfc822.html#section-6.1
            This explains what kind of value can be used for the "From" field in an email.
        """
        logger.debug(f"send_email called with email_job: {email_job}, send: {send}")
        try:
            # Determine SMTP settings and sender information
            sender = email_job._sender 
            if sender is None:
                sender = self.default_sender
                
                if sender is None:
                    logger.error("No sender information provided. Fallback to default sender failed.")
                    return

            msg = MIMEMultipart("alternative")
            msg["Subject"] = email_job._subject
            
            # Fix the 'From' header before assigning it
            fixed_from = fix_from_header(sender.get_sender_address())
            msg["From"] = fixed_from
            logger.debug(f"Email 'From' header set to: {msg['From']}")
            
            msg["To"] = ", ".join(email_job._recipients)
            logger.debug(f"Email 'To' header set to: {msg['To']}")
            
            # Add extra headers if provided, e.g., Reply-To
            if email_job._extra_headers:
                for key, value in email_job._extra_headers.items():
                    msg[key] = value
                    logger.debug(f"Added extra header: {key} = {value}")

            # Attach the body (plain or HTML)
            if email_job._body:
                msg.attach(MIMEText(email_job._body, "plain"))
                logger.debug("Attached plain text body to email.")
                
            if email_job._html:
                msg.attach(MIMEText(email_job._html, "html"))
                logger.debug("Attached HTML body to email.")

            # Send the email using SMTP
            with smtplib.SMTP(sender._email_server, sender._email_port) as server:
                if sender._use_tls:
                    server.starttls()
                    logger.debug("Started TLS for SMTP connection.")
                server.login(sender._username, sender._password)
                logger.debug("Logged into SMTP server.")
                
                # Convert message to string
                msg_string = msg.as_string(unixfrom=False)
                logger.debug(f"Email message string: {msg_string}")
                
                # Optionally write the email to a file for debugging
                with open("email.txt", "w") as f:
                    f.write(msg_string)
                    logger.debug("Wrote email message to email.txt for debugging.")

                # Send the email
                server.sendmail(sender._username, email_job._recipients, msg_string)
                logger.debug(f"Email sent to {email_job._recipients}")

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            # Optionally, requeue the email or log the error

    def register_filter(self, filter):
        def format_date(value):
            if isinstance(value, datetime):
                return value.strftime('%Y-%m-%d')  # Change format as needed
            return value

        # Register the custom filter with Jinja2
        self._env.filters['date'] = format_date
    
    def queue_email(self, template_name, subject, recipients, context, sender=None, extra_headers=None, send=True):
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
        extra_headers : dict, optional
            Additional headers to include in the email. Defaults to None.
        send : bool, optional
            If False, the email will not be sent. Defaults to True.
        """
        logger.debug(f"queue_email called with template_name: {template_name}, subject: {subject}, recipients: {recipients}, context: {context}, sender: {sender}, extra_headers: {extra_headers}, send: {send}")
        template = self._env.get_template(template_name)
        body = template.render(context)
        email_job = EmailJob(
            subject=subject, recipients=recipients, body=body, html=body, sender=sender, extra_headers=extra_headers
        )
        if send:
            self._queue_collection.insert_one(email_job.to_dict())
            logger.debug(f"Queued email to {recipients} with subject '{subject}'")
        else:
            logger.debug(f"Dry run: Email to {recipients} with subject '{subject}' not queued")

    def send_now(self, template_name, subject, recipients, context, sender=None, extra_headers=None, send=True):
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
        extra_headers : dict, optional
            Additional headers to include in the email. Defaults to None.
        send : bool, optional
            If False, the email will not be sent. Defaults to True.
        """
        logger.debug(f"send_now called with template_name: {template_name}, subject: {subject}, recipients: {recipients}, context: {context}, sender: {sender}, extra_headers: {extra_headers}, send: {send}")
        template = self._env.get_template(template_name)
        body = template.render(context)
        email_job = EmailJob(
            subject=subject, recipients=recipients, body=body, html=body, sender=sender, extra_headers=extra_headers
        )
        if send:
            self.send_email(email_job)
            logger.debug(f"Sent email to {recipients} with subject '{subject}'")
        else:
            logger.debug(f"Dry run: Email to {recipients} with subject '{subject}' not sent")


    def _die_when_done(self):
        """
        Waits for the email queue to become empty before stopping 
        the email queue worker thread.

        This method periodically checks if the email queue is empty. 
        Once there are no email jobs left, it exits the application.

        Returns
        -------
        None
        """
        logger.info("Waiting for the email queue to become empty before stopping the worker thread.")
        while self._queue_collection.count_documents({}) > 0:
            logger.debug("Email queue is not empty yet. Waiting...")
            time.sleep(1)
        logger.info("Email queue is empty. Stopping the worker thread.")
        exit(0)