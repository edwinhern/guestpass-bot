"""Discord modals for registration form input."""

import logging
from typing import TYPE_CHECKING, Optional

import discord

from src.config import config

if TYPE_CHECKING:
    from src.integrations.parking_registration_integration import ParkingRegistrationIntegration
    from src.services.registration_service import RegistrationService

logger = logging.getLogger(__name__)


class RegistrationModal(discord.ui.Modal, title="Guest Information"):
    """Modal form for collecting personal and basic vehicle information."""

    def __init__(
        self,
        service: "RegistrationService",
        integration: "ParkingRegistrationIntegration",
        discord_user_id: str,
    ) -> None:
        super().__init__()
        self.service = service
        self.integration = integration
        self.discord_user_id = discord_user_id
        self.registration_data: dict[str, Optional[str]] = {}

    # Personal Information
    first_name = discord.ui.TextInput(
        label="First Name",
        placeholder="John",
        required=True,
        max_length=100,
    )

    last_name = discord.ui.TextInput(
        label="Last Name",
        placeholder="Doe",
        required=True,
        max_length=100,
    )

    email = discord.ui.TextInput(
        label="Email",
        placeholder="john@example.com",
        required=True,
        max_length=255,
    )

    # Vehicle Information
    license_plate = discord.ui.TextInput(
        label="License Plate",
        placeholder="ABC1234",
        required=True,
        max_length=20,
    )

    license_plate_state = discord.ui.TextInput(
        label="License Plate State (2-letter code)",
        placeholder="CA",
        required=True,
        max_length=2,
        min_length=2,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Handle modal submission and show button for next step."""
        # Store data
        self.registration_data.update({
            "first_name": self.first_name.value,
            "last_name": self.last_name.value,
            "email": self.email.value,
            "license_plate": self.license_plate.value,
            "license_plate_state": self.license_plate_state.value,
        })

        # Create button to continue to vehicle details
        view = VehicleDetailsView(self.service, self.integration, self.discord_user_id, self.registration_data)
        await interaction.response.send_message(
            "✅ Guest information saved! Click below to continue:",
            view=view,
            ephemeral=True,
        )


class VehicleDetailsModal(discord.ui.Modal, title="Vehicle Details"):
    """Second modal for additional vehicle information."""

    def __init__(
        self,
        service: "RegistrationService",
        integration: "ParkingRegistrationIntegration",
        discord_user_id: str,
        registration_data: dict[str, Optional[str]],
    ) -> None:
        super().__init__()
        self.service = service
        self.integration = integration
        self.discord_user_id = discord_user_id
        self.registration_data = registration_data

    car_year = discord.ui.TextInput(
        label="Year",
        placeholder="2020",
        required=True,
        max_length=4,
        min_length=4,
    )

    car_make = discord.ui.TextInput(
        label="Make",
        placeholder="Toyota",
        required=True,
        max_length=50,
    )

    car_model = discord.ui.TextInput(
        label="Model",
        placeholder="Camry",
        required=True,
        max_length=50,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Handle modal submission and show color selector."""
        # Store data (without color - that comes next)
        self.registration_data.update({
            "car_year": self.car_year.value,
            "car_make": self.car_make.value,
            "car_model": self.car_model.value,
        })

        # Show color selector dropdown
        view = ColorSelectorView(self.service, self.integration, self.discord_user_id, self.registration_data)
        await interaction.response.send_message(
            "✅ Vehicle details saved!\n\n**Select your vehicle color from the dropdown below:**",
            view=view,
            ephemeral=True,
        )


class ColorSelectorView(discord.ui.View):
    """View with color dropdown selector."""

    def __init__(
        self,
        service: "RegistrationService",
        integration: "ParkingRegistrationIntegration",
        discord_user_id: str,
        registration_data: dict[str, Optional[str]],
    ) -> None:
        super().__init__(timeout=300)  # 5 minute timeout
        self.service = service
        self.integration = integration
        self.discord_user_id = discord_user_id
        self.registration_data = registration_data

    @discord.ui.select(
        placeholder="Choose your vehicle color",
        options=[
            discord.SelectOption(label="Black", value="Black", emoji="⚫"),
            discord.SelectOption(label="Blue", value="Blue", emoji="🔵"),
            discord.SelectOption(label="Brown", value="Brown", emoji="🟤"),
            discord.SelectOption(label="Gold", value="Gold", emoji="🟡"),
            discord.SelectOption(label="Gray", value="Gray", emoji="⚪"),
            discord.SelectOption(label="Green", value="Green", emoji="🟢"),
            discord.SelectOption(label="Orange", value="Orange", emoji="🟠"),
            discord.SelectOption(label="Pink", value="Pink", emoji="🩷"),
            discord.SelectOption(label="Purple", value="Purple", emoji="🟣"),
            discord.SelectOption(label="Red", value="Red", emoji="🔴"),
            discord.SelectOption(label="Silver", value="Silver", emoji="⚪"),
            discord.SelectOption(label="White", value="White", emoji="⚪"),
            discord.SelectOption(label="Yellow", value="Yellow", emoji="🟡"),
        ],
    )
    async def color_select(self, interaction: discord.Interaction, select: discord.ui.Select) -> None:
        """Handle color selection."""
        selected_color = select.values[0]

        # Store the color
        self.registration_data["car_color"] = selected_color

        # Show button to continue to visit information
        view = VisitInfoView(self.service, self.integration, self.discord_user_id, self.registration_data)
        await interaction.response.edit_message(
            content=f"✅ Color selected: **{selected_color}**\n\nClick below to continue:",
            view=view,
        )


class VisitInfoModal(discord.ui.Modal, title="Visit Information"):
    """Third modal for visit details."""

    def __init__(
        self,
        service: "RegistrationService",
        integration: "ParkingRegistrationIntegration",
        discord_user_id: str,
        registration_data: dict[str, Optional[str]],
    ) -> None:
        super().__init__()
        self.service = service
        self.integration = integration
        self.discord_user_id = discord_user_id
        self.registration_data = registration_data

    resident_visiting = discord.ui.TextInput(
        label="Resident Visiting (Full Name)",
        placeholder="Jane Smith",
        required=True,
        max_length=100,
    )

    apartment_visiting = discord.ui.TextInput(
        label="Apartment Number",
        placeholder="215",
        required=True,
        max_length=20,
        default=config.ppoa.default_apartment,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Handle final modal submission and create registration."""
        await interaction.response.defer(ephemeral=True)

        try:
            # Store final data
            self.registration_data.update({
                "resident_visiting": self.resident_visiting.value,
                "apartment_visiting": self.apartment_visiting.value,
            })

            # Create registration in database
            registration = self.service.create_registration(
                discord_user_id=self.discord_user_id,
                **self.registration_data,  # type: ignore[arg-type]
            )

            # Submit to PPOA
            await interaction.followup.send("Submitting registration to PPOA...", ephemeral=True)

            success, message = await self.integration.submit_registration(registration)

            if success:
                # Update submission tracking
                updated_reg = self.service.record_submission(registration.id)  # type: ignore[assignment]

                embed = discord.Embed(
                    title="✅ Registration Created and Submitted",
                    color=discord.Color.green(),
                    description=f"Registration #{updated_reg.id} created and submitted successfully!",
                )
                embed.add_field(name="Guest", value=f"{updated_reg.first_name} {updated_reg.last_name}")
                embed.add_field(
                    name="Vehicle",
                    value=f"{updated_reg.car_year} {updated_reg.car_make} {updated_reg.car_model}",
                )
                embed.add_field(name="Plate", value=f"{updated_reg.license_plate} ({updated_reg.license_plate_state})")
                embed.add_field(
                    name="Expires At",
                    value=updated_reg.expires_at.strftime("%Y-%m-%d %H:%M UTC") if updated_reg.expires_at else "N/A",
                )

                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                # Registration saved but submission failed
                await interaction.followup.send(
                    f"⚠️ Registration #{registration.id} saved but submission failed: {message}\n"
                    f"You can try resubmitting with `/resubmit {registration.id}`",
                    ephemeral=True,
                )

        except Exception as e:
            logger.exception("Error completing registration")
            await interaction.followup.send(f"Error: {e!s}", ephemeral=True)


# Button Views for chaining modals
class VehicleDetailsView(discord.ui.View):
    """View with button to show vehicle details modal."""

    def __init__(
        self,
        service: "RegistrationService",
        integration: "ParkingRegistrationIntegration",
        discord_user_id: str,
        registration_data: dict[str, Optional[str]],
    ) -> None:
        super().__init__(timeout=300)  # 5 minute timeout
        self.service = service
        self.integration = integration
        self.discord_user_id = discord_user_id
        self.registration_data = registration_data

    @discord.ui.button(label="Continue to Vehicle Details", style=discord.ButtonStyle.primary, emoji="🚗")
    async def continue_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Show the vehicle details modal."""
        modal = VehicleDetailsModal(self.service, self.integration, self.discord_user_id, self.registration_data)
        await interaction.response.send_modal(modal)


class VisitInfoView(discord.ui.View):
    """View with button to show visit information modal."""

    def __init__(
        self,
        service: "RegistrationService",
        integration: "ParkingRegistrationIntegration",
        discord_user_id: str,
        registration_data: dict[str, Optional[str]],
    ) -> None:
        super().__init__(timeout=300)  # 5 minute timeout
        self.service = service
        self.integration = integration
        self.discord_user_id = discord_user_id
        self.registration_data = registration_data

    @discord.ui.button(label="Continue to Visit Information", style=discord.ButtonStyle.primary, emoji="🏠")
    async def continue_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Show the visit information modal."""
        modal = VisitInfoModal(self.service, self.integration, self.discord_user_id, self.registration_data)
        await interaction.response.send_modal(modal)
