################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (14.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Drivers/stm32-max30102-master/max30102_for_stm32_hal.c 

OBJS += \
./Drivers/stm32-max30102-master/max30102_for_stm32_hal.o 

C_DEPS += \
./Drivers/stm32-max30102-master/max30102_for_stm32_hal.d 


# Each subdirectory must supply rules for building sources it contributes
Drivers/stm32-max30102-master/%.o Drivers/stm32-max30102-master/%.su Drivers/stm32-max30102-master/%.cyclo: ../Drivers/stm32-max30102-master/%.c Drivers/stm32-max30102-master/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_HAL_DRIVER -DSTM32F401xC -c -I../Core/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc/Legacy -I../Drivers/CMSIS/Device/ST/STM32F4xx/Include -I../Drivers/CMSIS/Include -I../USB_DEVICE/App -I../USB_DEVICE/Target -I../Middlewares/ST/STM32_USB_Device_Library/Core/Inc -I../Middlewares/ST/STM32_USB_Device_Library/Class/CDC/Inc -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Drivers-2f-stm32-2d-max30102-2d-master

clean-Drivers-2f-stm32-2d-max30102-2d-master:
	-$(RM) ./Drivers/stm32-max30102-master/max30102_for_stm32_hal.cyclo ./Drivers/stm32-max30102-master/max30102_for_stm32_hal.d ./Drivers/stm32-max30102-master/max30102_for_stm32_hal.o ./Drivers/stm32-max30102-master/max30102_for_stm32_hal.su

.PHONY: clean-Drivers-2f-stm32-2d-max30102-2d-master

