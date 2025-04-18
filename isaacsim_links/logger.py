import logging

logging.basicConfig(
    level=logging.INFO, format="[%(levelname)s] %(filename)s:%(lineno)d %(message)s"
)
logger = logging.getLogger("isaacsim_links")
