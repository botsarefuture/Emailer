def config_sender_converter(config):
    """Function to fetch the default sender configuration from the app configuration."""
    return {
        "email_server": config.get("EMAIL_SERVER"),
        "email_port": config.get("EMAIL_PORT"),
        "username": config.get("EMAIL_USERNAME"),
        "password": config.get("EMAIL_PASSWORD"),
        "use_tls": config.get("EMAIL_USE_TLS"),
        "email_address": config.get("EMAIL_ADDRESS"),
        "display_name": config.get("EMAIL_DISPLAY_NAME"),
    }

class Sender:
    """
    The Sender class encapsulates the information related to an email sender, including the
    SMTP server details and the sender's email credentials.

    Attributes
    ----------
    email_server : str
        The SMTP server address used to send emails.
    email_port : int
        The port to connect to the SMTP server.
    username : str
        The username for authenticating with the SMTP server.
    password : str
        The password for authenticating with the SMTP server.
    use_tls : bool
        A flag indicating whether to use TLS for the SMTP connection.
    email_address : str
        The sender's email address.
    display_name : str
        The display name of the sender.
    """

    def __init__(self, email_server, email_port, username, password, use_tls, email_address, display_name=None):
        """
        Initializes a new Sender instance with the given SMTP and sender details.

        Parameters
        ----------
        email_server : str
            The SMTP server address.
        email_port : int
            The port to connect to the SMTP server.
        username : str
            The username for SMTP authentication.
        password : str
            The password for SMTP authentication.
        use_tls : bool
            Whether to use TLS for the SMTP connection.
        email_address : str
            The sender's email address.
        display_name : str, optional
            The display name of the sender. Defaults to None.
        """
        self._email_server = email_server
        self._email_port = email_port
        self._username = username
        self._password = password
        self._use_tls = use_tls
        self._email_address = email_address
        self._display_name = display_name

    def to_dict(self):
        """
        Converts the Sender instance to a dictionary format.

        Returns
        -------
        dict
            A dictionary containing the sender information.
        """
        return {
            "email_server": self._email_server,
            "email_port": self._email_port,
            "username": self._username,
            "password": self._password,  # Note: Be careful with storing passwords!
            "use_tls": self._use_tls,
            "email_address": self._email_address,
            "display_name": self._display_name,
        }

    def get_sender_address(self):
        """
        Constructs the sender address including the display name if it exists.

        Returns
        -------
        str
            The sender address in the format "Display Name <email_address>" if display name exists,
            otherwise just the email address.
        """
        if self._display_name:
            return f"{self._display_name} <{self._email_address}>"
        return self._email_address

    @classmethod
    def from_dict(cls, data):
        """
        Creates a Sender instance from a dictionary.

        Parameters
        ----------
        data : dict
            A dictionary containing sender information.

        Returns
        -------
        Sender
            An instance of the Sender class.
        """
        return cls(
            email_server=data.get("email_server"),
            email_port=data.get("email_port"),
            username=data.get("username"),
            password=data.get("password"),  # Make sure passwords are handled securely!
            use_tls=data.get("use_tls"),
            email_address=data.get("email_address"),
            display_name=data.get("display_name"),
        )


class EmailJob:
    """
    The EmailJob class represents an email task, encapsulating all the details required to send an email.

    Attributes
    ----------
    subject : str
        The subject line of the email.
    recipients : list of str
        A list of recipient email addresses.
    body : str, optional
        The plain text body of the email.
    html : str, optional
        The HTML content of the email.
    sender : Sender, optional
        An instance of the Sender class containing the sender's information. Defaults to None.
    """

    def __init__(self, subject, recipients, body=None, html=None, sender=None):
        """
        Initializes an EmailJob instance with the provided details.

        Parameters
        ----------
        subject : str
            The subject of the email.
        recipients : list of str
            A list of recipient email addresses.
        body : str, optional
            The plain text body of the email. Defaults to None.
        html : str, optional
            The HTML content of the email. Defaults to None.
        sender : Sender, optional
            An instance of the Sender class. Defaults to None.
        """
        self._subject = subject
        self._recipients = recipients
        self._body = body
        self._html = html
        self._sender = sender  # Store a Sender instance if provided

    def to_dict(self):
        """
        Converts the EmailJob instance to a dictionary format for storage in a database.

        Returns
        -------
        dict
            A dictionary representation of the EmailJob instance.
        """
        return {
            "subject": self._subject,
            "recipients": self._recipients,
            "body": self._body,
            "html": self._html,
            "sender": self._sender.to_dict() if self._sender else None,
        }

    @classmethod
    def from_dict(cls, data):
        """
        Creates an EmailJob instance from a dictionary.

        Parameters
        ----------
        data : dict
            A dictionary containing email job details.

        Returns
        -------
        EmailJob
            An instance of the EmailJob class.
        """
        sender_data = data.get("sender")
        sender = Sender.from_dict(sender_data) if sender_data else None
        return cls(
            subject=data.get("subject"),
            recipients=data.get("recipients"),
            body=data.get("body"),
            html=data.get("html"),
            sender=sender,
        )
