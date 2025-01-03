from typing import Any, Optional, List, Literal
from pydantic import BaseModel, Field
from datetime import date as date_field
from xero_python.accounting import Contact, LineItem

class LineItemLLM(BaseModel):
    description: str = Field(description="A line item with just a description (i.e no unit amount or quantity) can be created by specifying just a Description element that contains at least 1 character")
    unit_amount: Optional[str] = Field(default=None, description="Unit price or rate per item, it may be empty if price is listed as line_amount")
    line_amount: Optional[str] = Field(default=None, description="Total item price, it may be empty if price is listed as line_amount")
    quantity: int = Field(default=1, description="Quantity of the item.")
    account_code: str = Field(description="This field is related to xero, the account code of expense category")
    account_id: str = Field(description="This field is related to xero, the account id of expense category")

    def as_xero(self) -> dict:
        return {
            "Description": self.description,
            "UnitAmount": self.unit_amount,
            "AccountCode": self.account_code,
            "Quantity": self.quantity,
            "LineAmount": self.line_amount
        }
        # LineItem(
        #     description=self.description,
        #     unit_amount=self.unit_amount,
        #     quantity=self.quantity,
        #     account_code=self.account_code,
        #     account_id=self.account_id
        # )
    # clarify it to prompt that other will be treated as line item such as admin fee
    
    # discount_rate: Optional[Any] = Field(None, description="Discount rate applied to the line item.")
    # discount_amount: Optional[Any] = Field(None, description="Discount amount applied to the line item.")
    
    # tax_rate: float = Field(description=f"The tax rate applied on the receipt")
    # tax_amount: Optional[Any] = Field(None, description="Amount of tax applied to the line item.")
    


class ReceiptLLM(BaseModel):
    receipt_from: Optional[str] = Field(description="The provider of the receipt")
    date: str = Field(description="Date of receipt – YYYY-MM-DD")
    reference: Optional[str] = Field(description="Additional reference number")
    
    # highlight this in prompt
    line_amount_types: Literal["Exclusive", "Inclusive", "NoTax"] = Field(description="The type of tax in the receipt")
    
    subtotal: str = Field(description="Total of receipt excluding taxes")
    total_tax: Optional[str] = Field(default=None, description="Total tax on receipt")
    
    total: str = Field(description="Total of receipt tax inclusive (i.e. SubTotal + TotalTax)")
    
    line_items: list[LineItemLLM] = Field(description="List of line item included in receipt")



class AccountLLM(BaseModel):
    account_id: str
    account_code: str
    account_name: str
    status: str
    type: str
    tax_type: str
    description: str