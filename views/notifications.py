import discord


class Notifications(discord.ui.Select):
    def __init__(self):

        # add emoji='🟩' attribute to SelectOption to add icons
        options = [
            discord.SelectOption(label='Уведомления о клозах по Dota 2', value='1147633914794479676'),
            discord.SelectOption(label='Уведомления о клозах по Valorant', value='1138235016917307432'),
        ]

        super().__init__(placeholder='Выберите уведомления', min_values=0, max_values=2, options=options)

    async def callback(self, interaction: discord.Interaction):
        """TODO: Optimize it"""
        await interaction.user.remove_roles(
            interaction.guild.get_role(1147633914794479676),
            interaction.guild.get_role(1138235016917307432)
        )

        for value in self.values:
            role = interaction.guild.get_role(int(value))
            await interaction.user.add_roles(role)

        embed = discord.Embed(description='Вы успешно **получили** роль')
        embed.set_author(name='Получение роли уведомлений', icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class NotificationsView(discord.ui.View):
    def __init__(self):
        super().__init__()

        notifications = Notifications()
        self.add_item(notifications)



