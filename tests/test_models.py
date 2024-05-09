from django.test import TestCase
from django.db import models

from libtekin.models import (
    Entity,
    EntityCategory,
    Item,
    ItemAssignee,
    ItemBorrower,
    ItemNote,
    ItemNoteCategory,
    ItemNoteLevel,
    Location,
    LocationCategory,
    Mmodel,
    MmodelCategory,
    Status,
)
from spl_members.models import Member

MODELS = (
    Entity,
    EntityCategory,
    Item,
    # ItemAssignee,
    # ItemBorrower,
    # ItemNote,
    # ItemNoteCategory,
    # ItemNoteLevel,
    # Location,
    # LocationCategory,
    # Mmodel,
    # MmodelCategory,
    # Status,
)


class GeneralModelTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.member_1 = Member.objects.create(name_full="member_1")
        cls.member_2 = Member.objects.create(name_full="member_2")

        cls.entity_1 = Entity.objects.create(full_name="entity_1")
        cls.item_1 = Item.objects.create(
            primary_id_field="serial_number",
            serial_number="item_1",
            assignee=cls.member_1,
            borrower=cls.member_2,
        )
        entity_category_1 = EntityCategory.objects.create(name="entity_category_1")

    def test_str(self):
        for model in MODELS:
            self.assertNotEqual(
                model.objects.first().__str__(),
                models.Model.__str__(model.objects.first()),
            )

    def test_item_assignee_created(self):
        item_assignee_1 = ItemAssignee.objects.first()
        self.assertEqual(item_assignee_1.item, self.item_1)
        self.assertEqual(item_assignee_1.assignee, self.item_1.assignee)

    def test_item_borrower_created(self):
        item_borrower_1 = ItemBorrower.objects.first()
        self.assertEqual(item_borrower_1.item, self.item_1)
        self.assertEqual(item_borrower_1.borrower, self.item_1.borrower)
