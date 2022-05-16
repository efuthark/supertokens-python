# Copyright (c) 2021, VRAI Labs and/or its affiliates. All rights reserved.
#
# This software is licensed under the Apache License, Version 2.0 (the
# "License") as published by the Apache Software Foundation.
#
# You may not use this file except in compliance with the License. You may
# obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from typing import Any, Dict

from supertokens_python.ingredients.emaildelivery.service.smtp import (
    EmailDeliverySMTPConfig, ServiceInterface, SMTPServiceConfigFrom,
    Transporter)
from supertokens_python.ingredients.emaildelivery.types import \
    EmailDeliveryInterface
from supertokens_python.recipe.emailpassword.types import \
    TypeEmailPasswordEmailDeliveryInput
from supertokens_python.recipe.emailverification.emaildelivery.service.smtp import \
    SMTPService as EmailVerificationSMTPService
from supertokens_python.recipe.emailverification.interfaces import \
    TypeEmailVerificationEmailDeliveryInput

from .service_implementation import ServiceImplementation
from .service_implementation.email_verification_implementation import \
    ServiceImplementation as EmailVerificationServiceImpl


class SMTPService(EmailDeliveryInterface[TypeEmailPasswordEmailDeliveryInput]):
    service_implementation: ServiceInterface[TypeEmailPasswordEmailDeliveryInput]

    def __init__(self, config: EmailDeliverySMTPConfig[TypeEmailPasswordEmailDeliveryInput]) -> None:
        self.config = config
        self.transporter = Transporter(config.smtp_settings)
        oi = ServiceImplementation(self.transporter)
        self.service_implementation = oi if config.override is None else config.override(oi)

        ev_config = EmailDeliverySMTPConfig[TypeEmailVerificationEmailDeliveryInput](
            smtp_settings=config.smtp_settings,
            override=lambda _: EmailVerificationServiceImpl(self.service_implementation)
        )
        self.email_verification_smtp_service = EmailVerificationSMTPService(ev_config)

    async def send_email(self, email_input: TypeEmailPasswordEmailDeliveryInput, user_context: Dict[str, Any]) -> None:
        if isinstance(email_input, TypeEmailVerificationEmailDeliveryInput):
            return await self.email_verification_smtp_service.send_email(email_input, user_context)

        content = await self.service_implementation.get_content(email_input, user_context)
        send_raw_email_from = SMTPServiceConfigFrom(
            self.config.smtp_settings.email_from.name,
            self.config.smtp_settings.email_from.email
        )
        await self.service_implementation.send_raw_email(content, send_raw_email_from, user_context)
