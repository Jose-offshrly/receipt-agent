from typing import Any, Optional, List, Literal
from pydantic import BaseModel, Field
from datetime import date as date_field
from xero_python.accounting import Contact, LineItem

class Address(BaseModel):
    AddressType: Optional[Literal['POBOX', 'STREET']] = Field(
        None, description="The type of address, POBOX for mailing addresses or STREET for physical addresses"
    )
    AddressLine1: Optional[str] = Field(
        None, description="First line of the address (e.g., street address or PO box)"
    )
    City: Optional[str] = Field(
        None, description="The city for the address"
    )
    Region: Optional[str] = Field(
        None, description="The region or state for the address"
    )
    PostalCode: Optional[str] = Field(
        None, description="The postal or ZIP code for the address"
    )
    Country: Optional[str] = Field(
        None, description="The country, using only alphabetic characters (A-Z, a-z)"
    )

class ContactLLM(BaseModel):
    Name: str = Field(description="Name of the business or individual.")
    Addresses: Optional[list[Address]] = Field(None, description="Addresses Info of the business or individual")
    EmailAddress: Optional[str] = Field(None, description="Email of the business or individual")


class LineItemLLM(BaseModel):
    Description: str = Field(description="A line item with just a description (i.e no unit amount or quantity) can be created by specifying just a Description element that contains at least 1 character")
    UnitAmount: Optional[str] = Field(default=None, description="Unit price or rate per item, it may be empty if price is listed as line_amount")
    LineAmount: Optional[str] = Field(default=None, description="Total item price, it may be empty if price is listed as line_amount")
    Quantity: int = Field(default=1, description="Quantity of the item.")
    AccountCode: str = Field(description="This field is related to xero, the account code of expense category")
    AccountId: str = Field(description="This field is related to xero, the account id of expense category")

    # def as_xero(self) -> dict:
    #     return {
    #         "Description": self.description,
    #         "UnitAmount": self.unit_amount,
    #         "AccountCode": self.account_code,
    #         "Quantity": self.quantity,
    #         "LineAmount": self.line_amount
    #     }
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
    # receipt_from: Optional[str] = Field(description="The provider of the receipt")
    Contact: ContactLLM = Field(description="Contact info of the business or individual.")
    Date: str = Field(description="Date of receipt – YYYY-MM-DD")
    Reference: Optional[str] = Field(description="Additional reference number")
    
    # highlight this in prompt
    LineAmountTypes: Literal["Exclusive", "Inclusive", "NoTax"] = Field(description="The type of tax in the receipt")
    
    SubTotal: str = Field(description="Total of receipt excluding taxes")
    TotalTax: Optional[str] = Field(default=None, description="Total tax on receipt")
    
    Total: str = Field(description="Total of receipt tax inclusive (i.e. SubTotal + TotalTax)")
    
    LineItems: list[LineItemLLM] = Field(description="List of line item included in receipt")



class AccountLLM(BaseModel):
    account_id: str
    account_code: str
    account_name: str
    status: str
    type: str
    tax_type: str
    description: str