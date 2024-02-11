import { TObject } from '@sinclair/typebox';
import addFormats from 'ajv-formats';
import Ajv from 'ajv';
import { ValidationError } from '../core/errors/error/validation.error';

const ajv = addFormats(new Ajv({}), [
  'date-time',
  'time',
  'date',
  'email',
  'hostname',
  'ipv4',
  'ipv6',
  'uri',
  'uri-reference',
  'uuid',
  'uri-template',
  'json-pointer',
  'relative-json-pointer',
  'regex',
]);

export function WithSchemaDecorator(schema: TObject): MethodDecorator {
  return function (
    target: any,
    propertyKey: string | symbol,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;
    const validator = ajv.compile(schema);

    if (descriptor.value.length !== 1) {
      throw new Error(
        `Method ${String(propertyKey)} of class ${
          target.constructor.name
        } must have exactly one argument`
      );
    }

    descriptor.value = async function (arg: any) {
      if (!validator(arg))
        throw new ValidationError(ajv.errorsText(validator.errors));
      return originalMethod.call(this, arg);
    };

    return descriptor;
  };
}
