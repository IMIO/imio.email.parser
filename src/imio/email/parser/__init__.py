from email.policy import default

import logging


email_policy = default

logger = logging.getLogger("imio.email.parser")
logger.setLevel(logging.INFO)
chandler = logging.StreamHandler()
chandler.setLevel(logging.INFO)
chandler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(chandler)
