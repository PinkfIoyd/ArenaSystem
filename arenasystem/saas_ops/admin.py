from django.contrib import admin

from .models import DataSubjectRequest, FeatureBlock, LegalConsent, LegalDocumentVersion, OperationalTask, SupportContact, SupportMessage, SupportTicket


admin.site.register(SupportTicket)
admin.site.register(SupportMessage)
admin.site.register(SupportContact)
admin.site.register(FeatureBlock)
admin.site.register(LegalDocumentVersion)
admin.site.register(LegalConsent)
admin.site.register(DataSubjectRequest)
admin.site.register(OperationalTask)

