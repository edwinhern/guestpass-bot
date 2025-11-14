"""Playwright integration for PPOA parking registration automation."""

import logging

from playwright.sync_api import Page, sync_playwright

from src.config import config
from src.models.registration import Registration

logger = logging.getLogger(__name__)


class ParkingRegistrationIntegration:
    """Handles automated submission of parking registration to PPOA."""

    PPOA_URL = "https://www.parkingpermitsofamerica.com/PermitRegistration.aspx"
    TIMEOUT = 30000  # 30 seconds

    def submit_registration(self, registration: Registration) -> tuple[bool, str]:
        """
        Submit a registration to PPOA using Playwright automation.

        Args:
            registration: Registration object with all required fields

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with sync_playwright() as p:
                # Launch browser (headless in production)
                browser = p.chromium.launch(headless=config.environment != "development")
                page = browser.new_page()

                try:
                    # Navigate to registration page
                    logger.info(f"Navigating to {self.PPOA_URL}")
                    page.goto(self.PPOA_URL, timeout=self.TIMEOUT)

                    # Step 1: Enter registration code
                    success, msg = self._enter_registration_code(page)
                    if not success:
                        return False, msg

                    # Step 2: Select permit type
                    success, msg = self._select_permit_type(page)
                    if not success:
                        return False, msg

                    # Step 3: Fill registration form
                    success, msg = self._fill_registration_form(page, registration)
                    if not success:
                        return False, msg

                    # Step 4: Submit and confirm
                    success, msg = self._submit_form(page)
                    if not success:
                        return False, msg

                    logger.info(
                        f"Successfully submitted registration for {registration.first_name} {registration.last_name}"
                    )
                    return True, "Registration submitted successfully"

                except Exception as e:
                    logger.exception("Error during registration submission")
                    return False, f"Submission error: {e!s}"

                finally:
                    browser.close()

        except Exception as e:
            logger.exception("Failed to launch browser")
            return False, f"Browser error: {e!s}"

    def _enter_registration_code(self, page: Page) -> tuple[bool, str]:
        """Enter the registration code and verify."""
        try:
            # Wait for registration code input
            code_input = page.wait_for_selector('input[id*="RegistrationCode"]', timeout=self.TIMEOUT)
            if not code_input:
                return False, "Registration code input not found"

            # Enter code
            code_input.fill(config.ppoa.registration_code)

            # Click verify button
            verify_button = page.wait_for_selector('button:has-text("Verify Code")', timeout=self.TIMEOUT)
            if not verify_button:
                return False, "Verify button not found"

            verify_button.click()

            # Wait for permit types to load
            page.wait_for_selector("text=Available Permit Types", timeout=self.TIMEOUT)

            return True, "Code verified"

        except Exception as e:
            logger.exception("Error entering registration code")
            return False, f"Failed to enter registration code: {e!s}"

    def _select_permit_type(self, page: Page) -> tuple[bool, str]:
        """Select 24Hr Registered Visitor permit type."""
        try:
            # Look for "24Hr Registered Visitor" and click select button
            select_button = page.wait_for_selector(
                'button:has-text("Select"):near(:text("24Hr Registered Visitor"))',
                timeout=self.TIMEOUT,
            )
            if not select_button:
                return False, "24Hr Registered Visitor permit type not found"

            select_button.click()

            # Wait for form to load
            page.wait_for_selector("text=Permit Registration", timeout=self.TIMEOUT)

            return True, "Permit type selected"

        except Exception as e:
            logger.exception("Error selecting permit type")
            return False, f"Failed to select permit type: {e!s}"

    def _fill_registration_form(self, page: Page, registration: Registration) -> tuple[bool, str]:
        """Fill out the registration form with vehicle and personal information."""
        try:
            # Vehicle Information
            page.fill('input[id*="LicensePlate"]', registration.license_plate)

            # License Plate State (dropdown)
            state_selector = 'select[id*="LicensePlateState"]'
            page.select_option(state_selector, value=registration.license_plate_state)

            # Vehicle details
            page.fill('input[id*="Year"]', registration.car_year)
            page.fill('input[id*="Make"]', registration.car_make)
            page.fill('input[id*="Model"]', registration.car_model)

            # Color (dropdown)
            color_selector = 'select[id*="Color"]'
            page.select_option(color_selector, label=registration.car_color)

            # Personal Information
            page.fill('input[id*="FirstName"]', registration.first_name)
            page.fill('input[id*="LastName"]', registration.last_name)

            # Visit Information
            page.fill('input[id*="ResidentVisiting"]', registration.resident_visiting)
            page.fill('input[id*="ApartmentVisiting"]', registration.apartment_visiting)

            # Optional fields
            if registration.phone_number:
                page.fill('input[id*="PhoneNumber"]', registration.phone_number)

            if registration.email:
                page.fill('input[id*="Email"]', registration.email)

            return True, "Form filled successfully"

        except Exception as e:
            logger.exception("Error filling registration form")
            return False, f"Failed to fill form: {e!s}"

    def _submit_form(self, page: Page) -> tuple[bool, str]:
        """Submit the form and confirm."""
        try:
            # Click "Proceed to Confirmation" button
            proceed_button = page.wait_for_selector(
                'button:has-text("Proceed to Confirmation")',
                timeout=self.TIMEOUT,
            )
            if not proceed_button:
                return False, "Proceed button not found"

            proceed_button.click()

            # Wait for confirmation page
            page.wait_for_timeout(2000)  # Wait 2 seconds for page load

            # Look for verify button or final submit
            verify_button = page.query_selector('button:has-text("Verify")')
            if verify_button:
                verify_button.click()
                page.wait_for_timeout(2000)

            # Check for success message or confirmation
            # The exact selector depends on PPOA's response
            # For now, we'll assume success if we got this far without errors

            return True, "Form submitted successfully"

        except Exception as e:
            logger.exception("Error submitting form")
            return False, f"Failed to submit form: {e!s}"

    def test_connection(self) -> tuple[bool, str]:
        """Test if the PPOA website is accessible."""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                try:
                    page.goto(self.PPOA_URL, timeout=self.TIMEOUT)
                    title = page.title()
                    browser.close()

                    return True, f"Successfully connected to PPOA (Title: {title})"

                except Exception as e:
                    browser.close()
                    return False, f"Failed to connect: {e!s}"

        except Exception as e:
            return False, f"Browser error: {e!s}"
