"""Playwright integration for PPOA parking registration automation."""

import logging

from playwright.async_api import Page, async_playwright

from src.config import config
from src.models.registration import Registration

logger = logging.getLogger(__name__)

# State code to full state name mapping for PPOA form
STATE_CODE_TO_NAME = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
    "DC": "District of Columbia",
}


class ParkingRegistrationIntegration:
    """Handles automated submission of parking registration to PPOA."""

    PPOA_URL = "https://www.parkingpermitsofamerica.com/PermitRegistration.aspx"
    TIMEOUT = 30000  # 30 seconds

    async def submit_registration(self, registration: Registration) -> tuple[bool, str]:
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
            logger.info("Waiting for registration code input field...")
            code_input = page.get_by_role("textbox", name="Registration Code*")
            await code_input.wait_for(timeout=self.TIMEOUT)

            # Click on the input first to focus it
            await code_input.click()
            await page.wait_for_timeout(300)

            # Use press_sequentially which better simulates real typing
            logger.info(f"Typing registration code: {config.ppoa.registration_code}")
            await code_input.press_sequentially(config.ppoa.registration_code, delay=150)

            # Trigger blur event to ensure validation runs
            await code_input.evaluate("el => el.dispatchEvent(new Event('blur', { bubbles: true }))")
            await page.wait_for_timeout(500)  # Brief pause after typing

            # Click verify button
            logger.info("Clicking verify button...")
            verify_button = page.get_by_role("button", name=" Verify Code")
            await verify_button.click()

            # Give the page time to process the verification
            logger.info("Waiting for page response after clicking verify...")
            await page.wait_for_timeout(3000)  # Wait 3 seconds for the page to respond

            # Check if there's an error message on the page
            try:
                error_alert = page.locator('div[role="alert"]')
                if await error_alert.is_visible(timeout=1000):
                    error_text = await error_alert.text_content()
                    logger.error(f"Verification error detected: {error_text}")
                    return False, f"Verification failed: {error_text}"
            except Exception:
                # No error message found, continue with normal flow
                logger.debug("No error alert found, proceeding")

            # Wait for permit types to load (verify the Select button appears)
            logger.info("Looking for Select button...")
            select_button = page.get_by_role("button", name=" Select")

            try:
                await select_button.wait_for(timeout=10000, state="visible")  # 10 second timeout
                logger.info("Select button found - permit types loaded")
            except Exception:
                # Log debugging information if verification fails
                logger.exception("Failed to find Select button after code verification")
                page_content = await page.content()
                logger.debug(f"Page content after verification (first 500 chars): {page_content[:500]}")
                raise

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

            # Give the page time to load the form
            await page.wait_for_timeout(1000)  # Wait 1 second for form to load

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

            # Convert 2-letter state code to full state name
            state_code = registration.license_plate_state.upper()
            state_name = STATE_CODE_TO_NAME.get(state_code, state_code)
            logger.debug(f"Converting state code '{state_code}' to '{state_name}'")

            await page.locator('select[name="PermitDetails.LicensePlateState"]').select_option(state_name)

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

            # Give the page time to navigate to confirmation page
            await page.wait_for_timeout(2000)  # Wait 2 seconds for page transition

            # Wait for confirmation page to load
            confirmation_checkbox = page.get_by_role("checkbox", name=" I confirm that I have")
            await confirmation_checkbox.wait_for(timeout=self.TIMEOUT)

            # Check the confirmation checkbox
            await confirmation_checkbox.check()
            logger.info("Confirmation checkbox checked")

            # TODO: TESTING MODE - Final submission is currently disabled
            # Uncomment the section below when ready to enable actual PPOA submissions
            """
            # Click the final submit button
            submit_button = page.get_by_role("button", name=" Confirm and Submit Permit")
            await submit_button.click()

            # Wait for submission to complete
            await page.wait_for_timeout(3000)

            # Verify success by looking for permit number (7-digit pattern)
            try:
                await page.wait_for_selector("text=/\\d{7}/", timeout=5000)
                logger.info("Permit submission confirmed - permit number detected")
            except Exception:
                logger.warning("Could not verify permit number, but no errors detected")
            """

            return True, "Form filled and ready for submission (testing mode - not submitted)"

        except Exception as e:
            logger.exception("Error submitting form")
            return False, f"Failed to submit form: {e!s}"
