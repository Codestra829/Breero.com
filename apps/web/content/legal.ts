export const legalBusiness = {
  brand: "Breero.com",
  operator: "Codestra LLC",
  dba: "Breero.com",
  corporateSite: "https://codestra.co",
  supportEmail: "support@breero.com",
  address: {
    line1: "20633 Longenbaugh Rd",
    city: "Cypress",
    region: "TX",
    postalCode: "77433",
    country: "United States",
  },
} as const;

export const legalIdentity = `${legalBusiness.operator} DBA ${legalBusiness.dba}`;
export const legalAddress = `${legalBusiness.address.line1}, ${legalBusiness.address.city}, ${legalBusiness.address.region} ${legalBusiness.address.postalCode}, ${legalBusiness.address.country}`;
