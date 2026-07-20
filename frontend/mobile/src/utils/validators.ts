import {
  SA_ID_NUMBER_REGEX,
  SA_MOBILE_NUMBER_REGEX,
  EMAIL_REGEX,
  PASSWORD_REGEX,
} from "@/constants/regex";

export const isValidSAIdNumber = (value: string) => SA_ID_NUMBER_REGEX.test(value);
export const isValidSAMobileNumber = (value: string) => SA_MOBILE_NUMBER_REGEX.test(value);
export const isValidEmail = (value: string) => EMAIL_REGEX.test(value);
export const isValidPassword = (value: string) => PASSWORD_REGEX.test(value);
