import random,secrets

def gen_order_id():
    id_length = 5
    characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    order_id= "".join(random.choice(characters)for i in range(id_length))
    return order_id