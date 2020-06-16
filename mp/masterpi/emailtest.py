from flask_mail import Mail, Message

def send_email(title,body):
    
    msg=Message(title, sender="l1093244975@gmail.com",recipients=["l1093244975@gmail.com","516539172@qq.com"])
    msg.body=body
    mail.send(msg)
