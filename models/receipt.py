from pydantic import BaseModel, Field

class Receipt(BaseModel):
    receipt_from: str = Field(description="The provider of the receipt")
    is_tax_included: bool = Field(description="Does the receipt include tax?")
    tax_type: str = Field(description=f"The type of tax included either: 'Tax Inclusive' or 'Tax Exclusive'. If none, 'Tax Exclusive'")
    date: str = Field(description="Date and time of the transaction")
    reference: str = Field(description="The reference of the receipt")
    description: str = Field(description="The description of the receipt")
    quantity: int = Field(description="The total quantity of items on the receipt")
    unit_price: float = Field(description="The total price of all receipt items")
    tax_rate: float = Field(description=f"The tax rate applied on the receipt")