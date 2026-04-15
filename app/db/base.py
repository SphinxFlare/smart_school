# db/base.py
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """
    The Single Source of Truth for the entire database metadata.
    """
    pass

# We import the "models" package from each domain.
# Because your __init__.py files in these folders already import 
# all individual models, these 7 lines register all 61+ tables.
from domains.academic import models as academic_models
from domains.identity import models as identity_models
from domains.admission import models as admission_models
from domains.finance import models as finance_models
from domains.transport import models as transport_models
from domains.welfare import models as welfare_models
from domains.communication import models as communication_models