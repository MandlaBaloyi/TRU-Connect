/**
 * Reserved integration point for messaging/notification delivery
 * providers. Ref: master prompt "External API Ready > Messaging"
 * (Twilio, WhatsApp Business API, Firebase Cloud Messaging) --
 * Notifications, OTP, Order Updates, Supplier Alerts, Delivery Updates.
 *
 * Not implemented yet. In-app notifications currently come from
 * GET /notifications (docs/05, Section 5.7). This module is where
 * push/SMS/WhatsApp delivery would be wired in for out-of-app alerts.
 */

export type MessagingChannel = "push" | "sms" | "whatsapp";

export async function sendMessage(_channel: MessagingChannel, _to: string, _body: string): Promise<never> {
  throw new Error(
    "messagingIntegration.sendMessage is not implemented yet -- see docs/08_PRODUCT_ROADMAP.txt"
  );
}
