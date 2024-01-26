import pywhatkit

# Limitation: install from source, current pip is broken.


def send_whatsapp_message(contact: str, message: str, group: bool = False):
    """Send WhatsApp Message to a person or group instantly

    Args:
        contact (str): In case of a group the link to the group chat, otherwise the phone number of the contact, should contain the country code.
        message (str): The message to be sent to the contact.
        group (bool, optional): Whether the message is to a group or not. Defaults to False.
    """
    try:
        if group:
            pywhatkit.sendwhatmsg_to_group_instantly(contact, message)
        else:
            pywhatkit.sendwhatmsg_instantly(contact, message)
        return "Message sent successfully!"
    except Exception as e:
        return f"Failed with error: {e}"


def main():
    send_whatsapp_message("+351912345678", "Hello World!")


if __name__ == "__main__":
    main()
