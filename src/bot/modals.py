"""Discord modals for registration form input."""

import discord

from src.config import config


class RegistrationModal(discord.ui.Modal, title="Guest Parking Registration"):
    """Modal form for collecting parking registration information."""

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

    phone_number = discord.ui.TextInput(
        label="Phone Number (Optional)",
        placeholder="555-1234",
        required=False,
        max_length=20,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Handle modal submission."""
        # This will be handled by the command that creates the modal
        await interaction.response.defer()


class VehicleDetailsModal(discord.ui.Modal, title="Vehicle Details"):
    """Second modal for additional vehicle information."""

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

    car_color = discord.ui.TextInput(
        label="Color",
        placeholder="Silver",
        required=True,
        max_length=30,
    )

    email = discord.ui.TextInput(
        label="Email (Optional)",
        placeholder="john@example.com",
        required=False,
        max_length=255,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Handle modal submission."""
        await interaction.response.defer()


class VisitInfoModal(discord.ui.Modal, title="Visit Information"):
    """Third modal for visit details."""

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
        """Handle modal submission."""
        await interaction.response.defer()
