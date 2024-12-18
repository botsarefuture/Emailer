import threading
import smtplib
import time
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from email.header import Header
from jinja2 import Environment, FileSystemLoader
from DatabaseManager import DatabaseManager
from .EmailJob import EmailJob, Sender

# Set up logger
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
    if from_address is None:
        return None

    # Handle the potential case where the 'From' address contains special characters or needs encoding
    name, address = from_address.split("<")
    address = address.replace(">", "")
    
    # Fix encoding if necessary
    name = name.strip()
    name_header = Header(name, "utf-8").encode()

    return formataddr((name_header, address))


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
            print(msg["From"])  # For debugging purposes
            
            msg["To"] = ", ".join(email_job._recipients)
            
            # Add extra headers if provided, e.g., Reply-To
            if email_job._extra_headers:
                for key, value in email_job._extra_headers.items():
                    msg[key] = value

            # Attach the body (plain or HTML)
            if email_job._body:
                msg.attach(MIMEText(email_job._body, "plain"))
                
            if email_job._html:
                msg.attach(MIMEText(email_job._html, "html"))

            # Send the email using SMTP
            with smtplib.SMTP(sender._email_server, sender._email_port) as server:
                if sender._use_tls:
                    server.starttls()
                server.login(sender._username, sender._password)
                
                # Convert message to string
                msg_string = msg.as_string(unixfrom=False)
                
                # Optionally write the email to a file for debugging
                with open("email.txt", "w") as f:
                    f.write(msg_string)

                # Send the email
                server.sendmail(sender._username, email_job._recipients, msg_string)
            
            logger.debug(f"Email sent to {email_job._recipients}")

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            # Optionally, requeue the email or log the error

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
