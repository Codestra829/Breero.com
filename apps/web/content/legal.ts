export const legalBusiness = {
  brand: "Breero.com",
  operator: "Codestra LLC",
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

// Do not describe BREERO as a registered DBA unless corporate records establish that status.
export const legalIdentity = `BREERO, operated by ${legalBusiness.operator}`;
export const legalAddress = `${legalBusiness.address.line1}, ${legalBusiness.address.city}, ${legalBusiness.address.region} ${legalBusiness.address.postalCode}, ${legalBusiness.address.country}`;
