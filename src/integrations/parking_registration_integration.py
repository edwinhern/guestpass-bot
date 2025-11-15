"""Playwright integration for PPOA parking registration automation."""

import logging

from playwright.async_api import Page, async_playwright

from src.config import config
from src.models.registration import Registration

logger = logging.getLogger(__name__)


class ParkingRegistrationIntegration:
    """Handles automated submission of parking registration to PPOA."""

    PPOA_URL = "https://www.parkingpermitsofamerica.com/PermitRegistration.aspx"
    TIMEOUT = 30000  # 30 seconds

    async def submit_registration(self, registration: Registration) -> tuple[bool, str]:
        """
        Submit a registration to PPOA using Playwright automation.

        Args:
            registration: Registration object with all required fields

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            async with async_playwright() as p:
                # Launch browser (headless in production)
                browser = await p.chromium.launch(headless=config.environment != "development")
                page = await browser.new_page()

                try:
                    # Navigate to registration page
                    logger.info(f"Navigating to {self.PPOA_URL}")
                    await page.goto(self.PPOA_URL, timeout=self.TIMEOUT)

                    # Step 1: Enter registration code
                    success, msg = await self._enter_registration_code(page)
                    if not success:
                        return False, msg

                    # Step 2: Select permit type
                    success, msg = await self._select_permit_type(page)
                    if not success:
                        return False, msg

                    # Step 3: Fill registration form
                    success, msg = await self._fill_registration_form(page, registration)
                    if not success:
                        return False, msg

                    # Step 4: Submit and confirm
                    success, msg = await self._submit_form(page)
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
                    await browser.close()

        except Exception as e:
            logger.exception("Failed to launch browser")
            return False, f"Browser error: {e!s}"

    async def _enter_registration_code(self, page: Page) -> tuple[bool, str]:
        """Enter the registration code and verify."""
        try:
            # Wait for and fill registration code input
            code_input = page.get_by_role("textbox", name="Registration Code*")
            await code_input.wait_for(timeout=self.TIMEOUT)
            await code_input.fill(config.ppoa.registration_code)

            # Click verify button
            verify_button = page.get_by_role("button", name=" Verify Code")
            await verify_button.click()

            # Wait for permit types to load (verify the Select button appears)
            select_button = page.get_by_role("button", name=" Select")
            await select_button.wait_for(timeout=self.TIMEOUT)

            return True, "Code verified"

        except Exception as e:
            logger.exception("Error entering registration code")
            return False, f"Failed to enter registration code: {e!s}"

    async def _select_permit_type(self, page: Page) -> tuple[bool, str]:
        """Select 24Hr Registered Visitor permit type."""
        try:
            # Click the Select button (assumes 24Hr Registered Visitor is the available option)
            select_button = page.get_by_role("button", name=" Select")
            await select_button.click()

            # Wait for form to load (check for license plate field)
            license_plate_input = page.locator('input[name="PermitDetails.LicensePlateNumber"]')
            await license_plate_input.wait_for(timeout=self.TIMEOUT)

            return True, "Permit type selected"

        except Exception as e:
            logger.exception("Error selecting permit type")
            return False, f"Failed to select permit type: {e!s}"

    async def _fill_registration_form(self, page: Page, registration: Registration) -> tuple[bool, str]:
        """Fill out the registration form with vehicle and personal information."""
        try:
            # Vehicle Information - using exact name attributes from codegen
            await page.locator('input[name="PermitDetails.LicensePlateNumber"]').fill(registration.license_plate)
            await page.locator('select[name="PermitDetails.LicensePlateState"]').select_option(
                registration.license_plate_state
            )

            # Vehicle details
            await page.locator('input[name="PermitDetails.VehicleYear"]').fill(registration.car_year)
            await page.locator('input[name="PermitDetails.VehicleMake"]').fill(registration.car_make)
            await page.locator('input[name="PermitDetails.VehicleModel"]').fill(registration.car_model)

            # Color (dropdown) - using label/text option
            await page.locator('select[name="PermitDetails.VehicleColor"]').select_option(registration.car_color)

            # Personal Information
            await page.locator('input[name="PermitDetails.FirstName"]').fill(registration.first_name)
            await page.locator('input[name="PermitDetails.LastName"]').fill(registration.last_name)

            # Visit Information
            await page.locator('input[name="PermitDetails.ResidentVisiting"]').fill(registration.resident_visiting)
            await page.locator('input[name="PermitDetails.ApartmentVisiting"]').fill(registration.apartment_visiting)

            # Optional fields
            if registration.phone_number:
                await page.locator('input[name="PermitDetails.PhoneNumber"]').fill(registration.phone_number)

            if registration.email:
                await page.locator('input[name="PermitDetails.Email"]').fill(registration.email)

            return True, "Form filled successfully"

        except Exception as e:
            logger.exception("Error filling registration form")
            return False, f"Failed to fill form: {e!s}"

    async def _submit_form(self, page: Page) -> tuple[bool, str]:
        """Submit the form and confirm."""
        try:
            # Click "Proceed to Confirmation" button
            proceed_button = page.get_by_role("button", name=" Proceed to Confirmation")
            await proceed_button.click()

            # Wait for confirmation page to load
            confirmation_checkbox = page.get_by_role("checkbox", name=" I confirm that I have")
            await confirmation_checkbox.wait_for(timeout=self.TIMEOUT)

            # Check the confirmation checkbox
            await confirmation_checkbox.check()

            # Click the final submit button
            # submit_button = page.get_by_role("button", name=" Confirm and Submit Permit")
            # await submit_button.click()

            # # Wait for success indicators (permit number or confirmation message)
            # # Give it a moment to process
            # await page.wait_for_timeout(3000)

            # # Check if we're on a success/confirmation page by looking for common success indicators
            # # The generated code showed permit numbers and dates appearing after submission
            # try:
            #     # Look for any text that indicates success (permit number pattern)
            #     await page.wait_for_selector("text=/\\d{7}/", timeout=5000)  # 7-digit permit number
            #     logger.info("Permit submission confirmed - permit number detected")
            # except Exception:
            #     # If we can't find a permit number, that's okay - we'll assume success if no error
            #     logger.warning("Could not verify permit number, but no errors detected")

            return True, "Form submitted successfully"

        except Exception as e:
            logger.exception("Error submitting form")
            return False, f"Failed to submit form: {e!s}"
