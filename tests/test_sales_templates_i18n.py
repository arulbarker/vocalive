"""Test sales_templates dengan i18n."""
import pytest

pytestmark = pytest.mark.unit


class TestSalesTemplatesI18n:
    def test_get_templates_returns_dict_with_keys(self, mocker):
        mocker.patch("modules_client.i18n._translations", {
            "sales_template.general_seller.name": "Penjual Umum",
            "sales_template.general_seller.description": "Template umum",
            "sales_template.general_seller.content": "Kamu adalah asisten live streaming...",
        })
        mocker.patch("modules_client.i18n._reference_translations", {})
        from sales_templates import get_templates
        templates = get_templates()
        assert "general_seller" in templates
        assert templates["general_seller"]["name"] == "Penjual Umum"

    def test_get_templates_reflects_current_language(self, mocker):
        mocker.patch("modules_client.i18n._translations", {
            "sales_template.general_seller.name": "General Seller",
            "sales_template.general_seller.description": "Generic template",
            "sales_template.general_seller.content": "You are a live streaming assistant...",
        })
        mocker.patch("modules_client.i18n._reference_translations", {})
        from sales_templates import get_templates
        templates = get_templates()
        assert templates["general_seller"]["name"] == "General Seller"

    def test_all_10_templates_present(self, mocker):
        # Build minimal keys for all 10 templates
        keys = {}
        for tkey in ["general_seller", "fashion_seller", "food_seller", "beauty_seller",
                     "electronics_seller", "household_seller", "baby_seller", "health_seller",
                     "digital_seller", "automotive_seller"]:
            keys[f"sales_template.{tkey}.name"] = f"{tkey}-name"
            keys[f"sales_template.{tkey}.description"] = f"{tkey}-desc"
            keys[f"sales_template.{tkey}.content"] = f"{tkey}-content"
        mocker.patch("modules_client.i18n._translations", keys)
        mocker.patch("modules_client.i18n._reference_translations", {})
        from sales_templates import get_templates
        templates = get_templates()
        assert len(templates) == 10
