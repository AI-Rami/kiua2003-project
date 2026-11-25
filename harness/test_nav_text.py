"""Synthetic, model-free checks for contact cleaning and the input screen."""

import unittest

from nav_text import clean_description, cleaned_input_issue


class ContactCleaningTests(unittest.TestCase):
    def test_contact_sentence_inside_mixed_paragraph(self):
        html = "<p>Du må kunne Python. Kontakt Kari Nord på kari@example.org eller 12345678.</p>"
        text, actions, reason = clean_description(html, [{"name": "Kari Nord"}])
        self.assertIsNone(reason)
        self.assertEqual(text, "Du må kunne Python. Kontakt Kari Nord på [redacted] eller [redacted].")
        self.assertIn("Kari Nord", text)
        self.assertEqual(actions, {"redacted_emails": 1, "redacted_phones": 1})

    def test_end_contact_without_heading(self):
        html = ("<p>Du må kunne Java.</p><p>Ved spørsmål om stillingen, "
                "ta kontakt med Kari Nord på 12345678.</p>")
        text, _, reason = clean_description(html)
        self.assertIsNone(reason)
        self.assertIn("Kari Nord på [redacted]", text)
        self.assertNotIn("12345678", text)

    def test_name_hint_only_does_not_remove_job_content(self):
        html = "<p>Kari Nord utvikler produktet. Du må kunne Python.</p>"
        text, actions, reason = clean_description(html, [{"name": "Kari Nord"}])
        self.assertIsNone(reason)
        self.assertIn("Kari Nord utvikler produktet.", text)
        self.assertEqual(sum(actions.values()), 0)

    def test_hinted_contact_name_without_number(self):
        html = "<p>Du må kunne SQL. Kari Nord kan svare på spørsmål om rollen.</p>"
        text, _, reason = clean_description(html, [{"name": "Kari Nord"}])
        self.assertIsNone(reason)
        self.assertIn("Kari Nord kan svare på spørsmål om rollen.", text)

    def test_common_contact_wording_at_end_without_number(self):
        html = "<p>Du må kunne SQL.</p><p>Ta gjerne kontakt med Kari Nord om rollen.</p>"
        text, _, reason = clean_description(html)
        self.assertIsNone(reason)
        self.assertIn("Ta gjerne kontakt med Kari Nord om rollen.", text)

    def test_english_reach_out_at_end(self):
        html = "<p>You must know Java.</p><p>Please reach out to Sam Lee about the role.</p>"
        text, _, reason = clean_description(html)
        self.assertIsNone(reason)
        self.assertIn("Please reach out to Sam Lee about the role.", text)

    def test_english_contact_and_qualification(self):
        html = "<p>Experience with Docker is required; please contact Sam Lee at sam@example.org.</p>"
        text, _, reason = clean_description(html)
        self.assertIsNone(reason)
        self.assertIn("Experience with Docker is required", text)
        self.assertIn("Sam Lee", text)
        self.assertNotIn("sam@example.org", text)

    def test_bold_contact_heading(self):
        html = ("<p>Du må kunne Linux.</p><p><strong>Contact</strong></p>"
                "<p>Sam Lee, sam@example.org</p><h2>Qualifications</h2><p>Docker is preferred.</p>")
        text, actions, reason = clean_description(html)
        self.assertIsNone(reason)
        self.assertIn("Du må kunne Linux.", text)
        self.assertIn("Docker is preferred.", text)
        self.assertNotIn("sam@example.org", text)
        self.assertGreater(sum(actions.values()), 0)

    def test_two_separate_contact_sections_and_phone_icon_suffix(self):
        html = ("<p>Du må kunne Python.</p>"
                "<p><strong>Kontaktinformasjon&nbsp;</strong></p>"
                "<p>Ta kontakt på test@example.org.</p>"
                "<p><strong>Kontaktperson for stillingen</strong></p>"
                "<p>Eksempel Person 12345678svg "
                "<a href='mailto:other@example.org'>other@example.org</a></p>"
                "<h2>Kvalifikasjoner</h2><p>SQL er ønskelig.</p>")
        text, actions, reason = clean_description(html)
        self.assertIsNone(reason)
        self.assertIn("Du må kunne Python.", text)
        self.assertIn("SQL er ønskelig.", text)
        self.assertNotIn("example.org", text)
        self.assertNotIn("12345678", text)
        self.assertGreater(sum(actions.values()), 0)

    def test_standalone_contact_person_heading(self):
        html = ("<p>Du må kunne Python.</p><h2>Kontaktperson for stillingen</h2>"
                "<p>Eksempel Person 12345678svg</p>")
        text, actions, reason = clean_description(html)
        self.assertIsNone(reason)
        self.assertIn("Eksempel Person [redacted]", text)
        self.assertGreater(sum(actions.values()), 0)

    def test_application_heading_ends_first_contact_section(self):
        html = ("<p>Du må kunne Python.</p>"
                "<p><strong>Kontaktinformasjon</strong></p><p>Ta kontakt på test@example.org.</p>"
                "<p><strong>Slik søker du</strong></p><p>Send søknaden via portalen.</p>"
                "<h2>Kontaktperson for stillingen</h2><p>Eksempel Person 12345678svg</p>")
        text, actions, reason = clean_description(html)
        self.assertIsNone(reason)
        self.assertIn("Du må kunne Python.", text)
        self.assertIn("Slik søker du", text)
        self.assertIn("Send søknaden via portalen.", text)
        self.assertNotIn("example.org", text)
        self.assertNotIn("12345678", text)
        self.assertEqual(actions, {"redacted_emails": 1, "redacted_phones": 1})

    def test_product_and_company_names_remain(self):
        text, _, reason = clean_description("<p>Du vil jobbe med Azure og GitHub hos Example Labs.</p>")
        self.assertIsNone(reason)
        self.assertIn("Azure og GitHub hos Example Labs", text)

    def test_uncertain_mixed_requirement_is_held(self):
        text, _, reason = clean_description("<p>Du må kunne Python og ringe 12345678.</p>")
        self.assertIsNone(text)
        self.assertEqual(reason, "uncertain_mixed_contact_passage")

    def test_contact_link_label_keeps_name_and_ignores_href(self):
        text, actions, reason = clean_description(
            '<a href="mailto:kari@example.org">Kari Nord</a>, tlf +47 999&nbsp;22&nbsp;333.')
        self.assertEqual(text, "Kari Nord, tlf [redacted].")
        self.assertEqual(actions["redacted_phones"], 1)
        self.assertIsNone(reason)

    def test_no_contact_values_in_referee_instructions(self):
        source = "Please supply the contact information of two referees."
        self.assertEqual(clean_description(source)[0], source)

    def test_preserve_dates_and_technical_text(self):
        source = "2026-11-25 (25.11.2026): SQL, ISO 27001 and C++."
        self.assertEqual(clean_description(source)[0], source)

    def test_contact_values_only_remain_unusable(self):
        self.assertEqual(clean_description("test@example.org / 12345678")[2], "no_safe_readable_text")

    def test_saved_text_screen_rejects_contact_details(self):
        self.assertEqual(cleaned_input_issue("Du må kunne Python. test@example.org"),
                         "remaining_email_or_phone")
        self.assertEqual(cleaned_input_issue("Du må kunne Python. Ring 12345678."),
                         "remaining_email_or_phone")
        self.assertIsNone(cleaned_input_issue("Du må kunne Python. Kontakt Kari Nord om rollen."))
        self.assertIsNone(cleaned_input_issue("Du må kunne Python hos Example Labs."))


if __name__ == "__main__":
    unittest.main()
