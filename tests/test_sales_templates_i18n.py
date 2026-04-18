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

    def test_content_follows_output_language_indonesia(self, mocker):
        """Audience split: UI=en tapi output=Indonesia → content harus Indonesian.

        name/description ikut ui_language, content ikut output_language.
        """
        # UI=English translations
        mocker.patch("modules_client.i18n._translations", {
            "sales_template.general_seller.name": "General Seller",
            "sales_template.general_seller.description": "English description",
            "sales_template.general_seller.content": "You are an English assistant...",
        })
        mocker.patch("modules_client.i18n._reference_translations", {})
        # output_language = Indonesia
        mocker.patch(
            "modules_client.config_manager.ConfigManager.get",
            side_effect=lambda k, d=None: "Indonesia" if k == "output_language" else d,
        )
        # Mock _load_json_file → locale lookup ("id") mengembalikan Indonesian content
        mocker.patch(
            "modules_client.i18n._load_json_file",
            return_value={
                "sales_template.general_seller.content": "Kamu adalah asisten Indonesia...",
            },
        )

        from sales_templates import get_templates
        templates = get_templates()

        # name & description → UI lang (English)
        assert templates["general_seller"]["name"] == "General Seller"
        assert templates["general_seller"]["description"] == "English description"
        # content → output_language (Indonesian)
        assert "Kamu adalah" in templates["general_seller"]["content"]

    def test_content_follows_output_language_english(self, mocker):
        """Audience split: UI=id tapi output=English → content harus English."""
        # UI=Indonesian translations
        mocker.patch("modules_client.i18n._translations", {
            "sales_template.general_seller.name": "Penjual Umum",
            "sales_template.general_seller.description": "Deskripsi Indonesia",
            "sales_template.general_seller.content": "Kamu adalah asisten Indonesia...",
        })
        mocker.patch("modules_client.i18n._reference_translations", {})
        # output_language = English
        mocker.patch(
            "modules_client.config_manager.ConfigManager.get",
            side_effect=lambda k, d=None: "English" if k == "output_language" else d,
        )
        # Mock _load_json_file → locale lookup ("en") mengembalikan English content
        mocker.patch(
            "modules_client.i18n._load_json_file",
            return_value={
                "sales_template.general_seller.content": "You are an English assistant...",
            },
        )

        from sales_templates import get_templates
        templates = get_templates()

        # name & description → UI lang (Indonesian)
        assert templates["general_seller"]["name"] == "Penjual Umum"
        # content → output_language (English)
        assert "You are an English" in templates["general_seller"]["content"]
