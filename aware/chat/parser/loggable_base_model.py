from pydantic import BaseModel


# TODO: Move to the logger? we can check if it is a pydantic model and use this method.
class LoggableBaseModel(BaseModel):
    def __str__(self):
        attrs = vars(self)
        return "\n".join(
            [f"{k}: {v}" for k, v in attrs.items() if (k != "__dict__" and v)]
        )
