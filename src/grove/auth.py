from djangosaml2.backends import Saml2Backend


def group_names(attributes: dict) -> set[str]:
    return {g.lower() for g in attributes.get('eduPersonEntitlement', ())}


class ModifiedSaml2Backend(Saml2Backend):

    def is_authorized(
        self,
        attributes: dict,
        attribute_mapping: dict,
        idp_entityid: str,
        assertion_info: dict,
        **kwargs,
    ) -> bool:
        return 'grove-user' in group_names(attributes)

    def _update_user(self, user, attributes: dict, attribute_mapping: dict, force_save: bool = False):
        groups = group_names(attributes)

        if 'grove-administrator' in groups:
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
        elif 'grove-user' in groups:
            user.is_staff = True
            user.is_superuser = False
            user.is_active = True
        else:
            user.is_staff = False
            user.is_superuser = False
            user.is_active = False

        return super()._update_user(user, attributes, attribute_mapping, force_save=True)
