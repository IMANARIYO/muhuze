import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

import type { PremiumPlan } from "../../types/premium";

/**
 * ==========================================
 * RECEIPT DATA
 * ==========================================
 */

interface ReceiptData {
  receiptNumber: string;

  customerName: string;

  customerEmail: string;

  paymentDate: string;

  plan: PremiumPlan;
}

/**
 * ==========================================
 * PREMIUM PDF RECEIPT SERVICE
 * ==========================================
 */

export class PDFReceiptService {
  generate(data: ReceiptData) {
    const doc = new jsPDF();

    /**
     * ========================================
     * HEADER
     * ========================================
     */

    doc.setFontSize(24);

    doc.setTextColor(25, 118, 210);

    doc.text(
      "MUHUZE",
      20,
      20
    );

    doc.setFontSize(14);

    doc.text(
      "Premium Membership Receipt",
      20,
      30
    );

    /**
     * ========================================
     * CUSTOMER INFORMATION
     * ========================================
     */

    doc.setFontSize(12);

    doc.text(
      `Receipt No: ${data.receiptNumber}`,
      20,
      45
    );

    doc.text(
      `Payment Date: ${data.paymentDate}`,
      20,
      53
    );

    doc.text(
      `Customer: ${data.customerName}`,
      20,
      61
    );

    doc.text(
      `Email: ${data.customerEmail}`,
      20,
      69
    );

    /**
     * ========================================
     * PLAN INFORMATION
     * ========================================
     */

    autoTable(doc, {
      startY: 80,

      head: [
        [
          "Description",
          "Duration",
          "Amount",
        ],
      ],

      body: [
        [
          `${data.plan.name} Premium Membership`,

          `${data.plan.duration} Days`,

          `${data.plan.price.toLocaleString()} USD`,
        ],
      ],
    });

    /**
     * ========================================
     * TOTAL
     * ========================================
     */

    const finalY =
      (doc as any).lastAutoTable.finalY + 15;

    doc.setFontSize(16);

    doc.text(
      `Total Paid: $${data.plan.price.toLocaleString()}`,
      20,
      finalY
    );

    /**
     * ========================================
     * PREMIUM BENEFITS
     * ========================================
     */

    doc.setFontSize(12);

    doc.text(
      "Premium Benefits",
      20,
      finalY + 20
    );

    /**
     * Build the benefits dynamically
     * from the actual Premium plan.
     */

    const benefits: string[] = [];

    const premiumBenefits =
      data.plan.benefits;

    /**
     * ----------------------------------------
     * GENERAL PREMIUM BENEFITS
     * ----------------------------------------
     */

    if (
      premiumBenefits.premiumBadge
    ) {
      benefits.push(
        "Premium Member Badge"
      );
    }

    if (
      premiumBenefits.priorityNotifications
    ) {
      benefits.push(
        "Priority Notifications"
      );
    }

    if (
      premiumBenefits.earlyPromotionAccess
    ) {
      benefits.push(
        "Early Access to Selected Promotions"
      );
    }

    if (
      premiumBenefits.premiumOnlyPromotions
    ) {
      benefits.push(
        "Access to Premium-Only Promotions"
      );
    }

    if (
      premiumBenefits.premiumDiscounts
    ) {
      benefits.push(
        "Special Premium Member Discounts"
      );
    }

    if (
      premiumBenefits.enhancedFavorites
    ) {
      benefits.push(
        "Enhanced Favorites / Watchlist"
      );
    }

    if (
      premiumBenefits.prioritySupport
    ) {
      benefits.push(
        "Priority Customer Support"
      );
    }

    if (
      premiumBenefits.priorityServiceHandling
    ) {
      benefits.push(
        "Priority Handling for Eligible MUHUZE Services"
      );
    }

    /**
     * ----------------------------------------
     * REFERRAL BENEFIT
     * ----------------------------------------
     */

    if (
      premiumBenefits.referralCommissionEligible
    ) {
      benefits.push(
        "Eligible to Participate in the Referral Commission Program"
      );
    }

    /**
     * ----------------------------------------
     * SELLER BENEFITS
     * ----------------------------------------
     */

    if (
      premiumBenefits.enhancedVisibility
    ) {
      benefits.push(
        "Increased Product Visibility"
      );
    }

    if (
      premiumBenefits.promotionalAdvantages
    ) {
      benefits.push(
        "Seller Promotional Advantages"
      );
    }

    if (
      premiumBenefits.advancedAnalytics
    ) {
      benefits.push(
        "Advanced Seller Analytics"
      );
    }

    if (
      premiumBenefits.unlimitedListings
    ) {
      benefits.push(
        "Unlimited Product Listings"
      );
    }

    if (
      premiumBenefits.sellerVerificationEligible
    ) {
      benefits.push(
        "Premium Seller Verification Eligibility"
      );
    }

    /**
     * ----------------------------------------
     * SELLER COMMISSION
     * ----------------------------------------
     *
     * Basic seller = 12%
     * Premium seller = 7%
     */

    benefits.push(
      `Premium Seller Commission Rate: ${premiumBenefits.sellerCommissionRate}%`
    );

    /**
     * ========================================
     * PRINT BENEFITS
     * ========================================
     */

    benefits.forEach(
      (benefit, index) => {
        doc.text(
          `• ${benefit}`,
          25,
          finalY + 30 + index * 8
        );
      }
    );

    /**
     * ========================================
     * REFERRAL DISCLAIMER
     * ========================================
     *
     * Premium does NOT guarantee income.
     */

    const disclaimerY =
      finalY +
      30 +
      benefits.length * 8 +
      10;

    doc.setFontSize(9);

    doc.setTextColor(
      100,
      100,
      100
    );

    doc.text(
      "Referral commission eligibility does not guarantee income.",
      20,
      disclaimerY
    );

    doc.text(
      "Commissions require qualifying MUHUZE economic activity and eligible revenue.",
      20,
      disclaimerY + 6
    );

    /**
     * ========================================
     * FOOTER
     * ========================================
     */

    doc.setTextColor(
      120,
      120,
      120
    );

    doc.text(
      "MUHUZE Global Link",
      20,
      disclaimerY + 20
    );

    /**
     * ========================================
     * SAVE RECEIPT
     * ========================================
     */

    doc.save(
      `MUHUZE-Receipt-${data.receiptNumber}.pdf`
    );
  }
}